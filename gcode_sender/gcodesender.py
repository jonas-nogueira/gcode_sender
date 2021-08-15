
import serial
import time
import argparse
from functools import reduce
from enum import Enum


class GCodeResponse(Enum):
    OK = 1
    ERROR = 2


class GCodeSenderStatus(Enum):
    READY = 1
    ERROR = 2
    FINISHED = 3


class GCodeSender:
    def __init__(self, serial: serial.Serial, gcode_list: list[str]) -> None:
        self.serial = serial
        self.command_queue = gcode_list
        self.resend_limit = 3
        self.current_line = 0
        self.resent = 0
        self.status = GCodeSenderStatus.READY

    def _has_next(self) -> bool:
        if self.current_line < len(self.command_queue):
            return True
        return False

    def _handle_response(self, response: str) -> GCodeResponse:
        if response.startswith("Error"):
            return GCodeResponse.ERROR
        return GCodeResponse.OK

    def _send_next(self) -> None:
        if(self._has_next()):
            self.serial.write(
                self.command_queue[self.current_line].encode("UTF-8"))
            response = self.serial.readline().decode("UTF-8").strip()
            response_result = self._handle_response(response)
            if response_result == GCodeResponse.OK:
                print(f">>> {self.command_queue[self.current_line].strip()}")
                print(f"<<<   {response}")
                self.current_line += 1
                self.resent = 0
            elif self.resent < self.resend_limit - 1:
                self.resent += 1
                print(f"Resending command -{self.resent}-")
            else:
                self.status = GCodeSenderStatus.ERROR
        else:
            self.status = GCodeSenderStatus.FINISHED

    def start(self) -> None:
        self.serial.write("\r\n\r\n".encode("UTF-8"))
        time.sleep(2)
        self.serial.reset_input_buffer()

        for command in self.command_queue:
            if self.status == GCodeSenderStatus.FINISHED:
                print("Print finished!")
                return
            if self.status == GCodeSenderStatus.ERROR:
                print("Print Error!")
                return
            self._send_next()


def checksum(command):
    return reduce(lambda x, y: x ^ y, map(ord, command))


def format_command(command: str) -> str:
    formated_command = f"{command}\n"
    return formated_command


parse = argparse.ArgumentParser(description="this is a basic gcode sender!")
parse.add_argument("-f", "--file", help="GCode file name", required=True)
args = parse.parse_args()

with serial.Serial('/dev/ttyUSB0', 115200, timeout=1) as ser:
    print(f'USB port: {ser.name}')
    with open(args.file, 'r') as file:
        commands = []

        for line in file:
          line = line.strip()
          if(line.isspace() == False and len(line) > 0):
            commands.append(format_command(line))

        gcode_sender = GCodeSender(ser, commands)
        gcode_sender.start()
