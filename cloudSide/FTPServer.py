from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer  # thread based
from pyftpdlib.authorizers import DummyAuthorizer


def main():
    authorizer = DummyAuthorizer()
    authorizer.add_user('user', '12345', './space_file', perm='elradfmwMT')
    handler = FTPHandler
    handler.authorizer = authorizer
    server = ThreadedFTPServer(('192.168.2.102', 2121), handler)
    server.serve_forever()

if __name__ == "__main__":
    main()
