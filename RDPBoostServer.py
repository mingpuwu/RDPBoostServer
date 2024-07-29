import socket
import threading
import RDPBoost_pb2

# 服务器地址和端口
HOST = '0.0.0.0'  # 服务器的地址，这里使用本地地址
PORT = 21220        # 服务器的端口号

datalist = []
lock = threading.Lock()
recvBuffer = None

def Handler_serverData(data):
    with lock:
        datalist.append(data)

def Handler_clientData(client_socket, TestData):
    onedata = None
    sent_length = 0

    onedata = TestData.read(4096)
    if len(onedata) == 0:
        print("read file eof, close it")
        return -1

    # with lock:
    #     onedata = datalist.pop()

    while sent_length < len(onedata):
        sent_bytes = client_socket.send(onedata[sent_length:])
        if sent_bytes is None:
            return -1
        sent_length += sent_bytes

    return 0

def Handler_clientData2(client_socket, TestData):
    PMessage = RDPBoost_pb2.ProtoMessage()
    ParseData = None

    data = client_socket.read(4096)
    if(recvBuffer is not None and len(recvBuffer) != 0):
        recvBuffer.append(data)

        if(PMessage.ParseFromString(recvBuffer) is True):
            print("ParseFromString success")
            recvBuffer = None
        else:
            print("ParseFromString error,wait next data")
            if(len(recvBuffer) > 2074600):
                recvBuffer = None
    

def handle_client(client_socket, client_address):
    print(f"接收到来自 {client_address} 的连接")

    PMessage = RDPBoost_pb2.ProtoMessage()
    print("wait recv message")
    recvdata = client_socket.recv(1024)
    print("recv data")
    PMessage.ParseFromString(recvdata)

    print("Einfo.type:",PMessage.type)
    if(PMessage.type == RDPBoost_pb2.ProtoMessage.DataType.ENDPOINT_INFO):
        if(PMessage.EndPointInfoI.type == RDPBoost_pb2.EndPointInfo.EndPointType.IS_SERVER):
            print("is server")
            Server = True
        else:
            print("is client")
            Server = False 

    if Server is False:
        TestData = open("TestH264Record.video",'rb')

    while True:
        try:
            if Server is True:
                data = client_socket.recv(1024)
                if not data:
                    break  # 如果没有接收到数据，跳出循环
                Handler_serverData(data)
            else:
                if(Handler_clientData2(client_socket, TestData) < 0):
                    print("close socket")
                    break

        except Exception as e:
            print(f"处理客户端连接时发生错误: {e}")
            break

    print(f"断开与 {client_address} 的连接")
    if TestData:
        TestData.close()
        TestData = None
    client_socket.close()

if __name__ == "__main__":

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"服务器启动，等待连接... {HOST}:{PORT}")

    while True:
        # 接受客户端的连接
        print('wait connect')
        client_socket, client_address = server_socket.accept()
        # 多线程处理客户端连接
        client_thread = threading.Thread(target=handle_client, 
                                         args=(client_socket, client_address))
        client_thread.start()