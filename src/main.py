import logging
import socket

import sm_driver
from PiService import AtmServiceFactory
from Wallet import Wallet
from banknote_transfer import transfer_banknotes

errors = set()


def handle_client_connection():
    logging.debug("client connected")

    def on_bucks_inserted(pulse_count):
        service.client_sock.setblocking(True)
        transfer_banknotes(service, wallet, pulse_count)
        service.client_sock.setblocking(False)

    sm_driver.set_active(is_active=True)

    service.client_sock.setblocking(False)

    for _ in sm_driver.update_loop(callback=on_bucks_inserted, verbose=True):
        if service.client_sock.getblocking():
            continue

        try:
            msg = service.client_sock.recv(1024)
            print(msg)
        except socket.error as e:
            errors.add(str(e))
        except BaseException as e:
            errors.add(str(e))


if __name__ == "__main__":
    wallet = Wallet()
    wallet.refill(10000)

    service = AtmServiceFactory.create_tcp_socket()
    sm_driver.initialise_pins()

    try:
        for client_sock in service.listen_for_connections():
            try:
                handle_client_connection()
            except Exception as e:
                logging.error("client disconnected", exc_info=e)
                print(errors)
                sm_driver.set_active(is_active=False)
    except Exception as e:
        service.stop()
        logging.critical("catched error:", exc_info=e)
    except KeyboardInterrupt:
        service.stop()
        logging.warning("Interrupted: socket closed")
