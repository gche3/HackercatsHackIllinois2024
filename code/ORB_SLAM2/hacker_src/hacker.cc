#include<iostream>
#include<algorithm>
#include<fstream>
#include<chrono>
#include<string>
#include<unistd.h>
#include<pthread.h>
#include <csignal>

#include <boost/beast/core.hpp>
#include <boost/beast/http.hpp>
#include <boost/beast/version.hpp>
#include <boost/asio/connect.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <cstdlib>
#include <iostream>
#include <string>

namespace beast = boost::beast;     // from <boost/beast.hpp>
namespace http = beast::http;       // from <boost/beast/http.hpp>
namespace net = boost::asio;        // from <boost/asio.hpp>
using tcp = net::ip::tcp;           // from <boost/asio/ip/tcp.hpp>

#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/prettywriter.h"
using namespace rapidjson;

#include<opencv2/core/core.hpp>
#include <opencv2/highgui.hpp>
#include<opencv2/imgcodecs/legacy/constants_c.h>

#include<System.h>

using namespace std;

typedef struct grab_arg {
    string host;
    string port;
    string endpoint;
    cv::Mat& latest_img;
    double& latest_time;
} grab_arg;

pthread_mutex_t mtx;
bool should_exit = false;

static inline bool is_base64(unsigned char c);
std::string base64_decode(std::string const& encoded_string);

void* grabImages(void* arg);

void intHandler(int sig);

int main(int argc, char **argv)
{

    if(argc != 7)
    {
        cerr << endl << "Usage: ./hacker host port get_endpoint post_endpoint vocab config" << endl;
        return 1;
    }
    std::signal(SIGINT, intHandler);

    ORB_SLAM2::System SLAM(argv[5],argv[6],ORB_SLAM2::System::MONOCULAR,true);

    mtx = PTHREAD_MUTEX_INITIALIZER;
    pthread_t grab_thread;
    cv::Mat latest_image;
    double latest_time = 0;
    double prev_time = latest_time;
    grab_arg arg = {argv[1], argv[2], argv[3], latest_image, latest_time};
    pthread_create(&grab_thread, nullptr, grabImages, &arg);

    // Setting up request and stream for sending post back
    net::io_context ioc;
    tcp::resolver resolver(ioc);
    auto const results = resolver.resolve(argv[1], argv[2]);
    beast::tcp_stream stream(ioc);
    
    http::request<http::string_body> req{http::verb::post, argv[4], 11};
    req.set(beast::http::field::content_type, "text/json");
    
    while(!should_exit) {
        pthread_mutex_lock(&mtx);
        if (latest_time == prev_time) {
            pthread_mutex_unlock(&mtx);
            continue;
        }
        // Make copies of the variables so that the image grabber can keep grabbing
        prev_time = latest_time;
        cv::Mat image_to_anal = latest_image;
        pthread_mutex_unlock(&mtx);
        cv::Mat pose = SLAM.TrackMonocular(image_to_anal, prev_time);
        
        if (pose.total() > 0) {
            // Send pose to server if we get a valid pose
            std::ostringstream os; 
            os << pose.reshape(0, 1);    
            
            Document document;
            document.SetObject();
            document.AddMember("pose", os.str(), document.GetAllocator());
            document.AddMember("time", prev_time, document.GetAllocator());
            StringBuffer req_buf;
            PrettyWriter<StringBuffer> writer(req_buf);
            document.Accept(writer);

            req.body() = req_buf.GetString();
            req.prepare_payload();
            stream.connect(results);
            http::write(stream, req);
        } else {
            std::cout << "No pose available, trying to localize / relocalize..." << std::endl;
        }
        beast::error_code ec;
        stream.socket().shutdown(tcp::socket::shutdown_both, ec);
    }
    
    SLAM.Shutdown();
    pthread_mutex_destroy(&mtx);
    pthread_join(grab_thread, nullptr);
    return 0;
}

void* grabImages(void* arg) {
    grab_arg* arg_struct = (grab_arg*) arg;
    auto const host = arg_struct->host;
    auto const port = arg_struct->port;
    auto const endpoint = arg_struct->endpoint;
    int version = 11;

    // The io_context is required for all I/O
    net::io_context ioc;

    // These objects perform our I/O
    tcp::resolver resolver(ioc);
    beast::tcp_stream stream(ioc);

    // Look up the domain name
    auto const results = resolver.resolve(host, port);

    // Set up an HTTP GET request message
    http::request<http::string_body> req{http::verb::get, endpoint, version};
    req.set(http::field::host, host);
    req.set(http::field::user_agent, BOOST_BEAST_VERSION_STRING);
    req.keep_alive(true);

    // This buffer is used for reading and must be persisted
    beast::flat_buffer buffer;

    while (!should_exit) {
        try
        {
            // Make the connection on the IP address we get from a lookup
            stream.connect(results);
            // Declare a container to hold the response
            http::response<http::dynamic_body> res;
            // Send the HTTP request to the remote host
            http::write(stream, req);
            // Receive the HTTP response
            http::read(stream, buffer, res);
            
            Document res_parsed;
            res_parsed.Parse(beast::buffers_to_string(res.body().data()).c_str());
            std::string image_str = res_parsed["image"].GetString();

            // Write the message to standard out
            std::string image_str_decoded = base64_decode(image_str);
            std::vector<uchar> image_vec(image_str_decoded.begin(), image_str_decoded.end());

            pthread_mutex_lock(&mtx);
            arg_struct->latest_img = cv::imdecode(image_vec, cv::IMREAD_UNCHANGED);
            arg_struct->latest_time = res_parsed["time"].GetDouble();
            // std::cout << arg_struct->latest_img << std::endl;
            pthread_mutex_unlock(&mtx);

                        // Gracefully close the socket
            beast::error_code ec;
            stream.socket().shutdown(tcp::socket::shutdown_both, ec);

            // not_connected happens sometimes
            // so don't bother reporting it.
            //
            if(ec && ec != beast::errc::not_connected)
                throw beast::system_error{ec};
        }
        catch(std::exception const& e)
        {
            std::cerr << "Image grab error: " << e.what() << std::endl;
            continue;
        }
    }

    // If we get here then the connection is closed gracefully
    return nullptr;   
}

void intHandler(int sig) {
    should_exit = true;
}

// Code from: http://www.adp-gmbh.ch/cpp/common/base64.html

static const std::string base64_chars =
"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
"abcdefghijklmnopqrstuvwxyz"
"0123456789+/";


static inline bool is_base64(unsigned char c) {
    return (isalnum(c) || (c == '+') || (c == '/'));
}

std::string base64_decode(std::string const& encoded_string) {
    int in_len = encoded_string.size();
    int i = 0;
    int j = 0;
    int in_ = 0;
    unsigned char char_array_4[4], char_array_3[3];
    std::string ret;

    while (in_len-- && (encoded_string[in_] != '=') && is_base64(encoded_string[in_])) {
        char_array_4[i++] = encoded_string[in_]; in_++;
        if (i == 4) {
            for (i = 0; i < 4; i++)
                char_array_4[i] = base64_chars.find(char_array_4[i]);

            char_array_3[0] = (char_array_4[0] << 2) + ((char_array_4[1] & 0x30) >> 4);
            char_array_3[1] = ((char_array_4[1] & 0xf) << 4) + ((char_array_4[2] & 0x3c) >> 2);
            char_array_3[2] = ((char_array_4[2] & 0x3) << 6) + char_array_4[3];

            for (i = 0; (i < 3); i++)
                ret += char_array_3[i];
            i = 0;
        }
    }

    if (i) {
        for (j = i; j < 4; j++)
            char_array_4[j] = 0;

        for (j = 0; j < 4; j++)
            char_array_4[j] = base64_chars.find(char_array_4[j]);

        char_array_3[0] = (char_array_4[0] << 2) + ((char_array_4[1] & 0x30) >> 4);
        char_array_3[1] = ((char_array_4[1] & 0xf) << 4) + ((char_array_4[2] & 0x3c) >> 2);
        char_array_3[2] = ((char_array_4[2] & 0x3) << 6) + char_array_4[3];

        for (j = 0; (j < i - 1); j++) ret += char_array_3[j];
    }

    return ret;
}
