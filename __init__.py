# Copyright 2019 Linus S.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import threading
import py2p
from mycroft import MycroftSkill, intent_file_handler
from mycroft.api import DeviceApi
import json
import time

from . import shippingHandling


class Communications(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.calling = False

    def initialize(self):
        self.add_event('skill.communications.intercom.new',
                       self.handle_new_intercom)
        self.add_event('skill.communications.device.new',
                       self.handle_new_device)
        # Start the server/ get the socket
        self.sock = py2p.MeshSocket("0.0.0.0", 4445)
        self.log.info("Starting the receiving loop...")
        # Start up a new thread for receiving messages
        device = DeviceApi().get()
        r = threading.Thread(target=shippingHandling.start_receiving_Loop, args=(self.sock, device["uuid"],), daemon=True)  # nopep8
        r.start()
        # Auto connect to others:
        # Start new advertisement thread
        self.log.info("Starting the device advertisement thread...")
        a = threading.Thread(target=shippingHandling.start_advertisement_loop, args=(device["name"],), daemon=True)
        a.start()
        # Begin Listener thread
        self.log.info("Starting the listener thread...")
        L = threading.Thread(target=shippingHandling.start_new_service_listener_loop, args=(self.sock,), daemon=True)
        L.start()

    def send_intercom(self, message):
        """Send messages to all other devices
        """
        device = DeviceApi().get()
        shippingHandling.send_message(self.sock, message, message_type="intercom",
                                      mycroft_id=device["uuid"], mycroft_name=device["name"])

    def handle_new_intercom(self, message):
        """A intercom was called"""
        # Get the announcement
        announcement = json.loads(message.data.get("message"))["data"]
        self.log.info("New intercom announcement incoming!: {}".format(announcement))
        # Make a BLING sound (Might want to change this)
        self.acknowledge()
        self.speak_dialog("new.intercom", data={"message": announcement})

    def handle_new_device(self, message):
        ip = message.data.get("message")
        self.log.info("New Mycroft Communications device at: {}".format(ip))
        self.sock.connect(str(ip), 4445)
        self.log.info("Done connecting to device")

    @intent_file_handler('broadcast.intercom.intent')
    def handle_intercom(self, message):
        # Get the announcement
        announcement = message.data.get("announcement")
        while not announcement:
            announcement = self.get_response("get.new.announcement.name")

        # OKay, we got the announcement
        # Time to send the message to all...
        self.send_intercom(announcement)
        self.speak_dialog('broadcasting.intercom')

    @intent_file_handler('new.call.intent')
    def handle_call(self, message):
        """Handle calling between devices"""
        # Get the device name
        name = message.data.get("name")
        while not name:
            name = self.get_response("get.name")
        # TODO: Search for name
        # TODO: Say no if there is not a active device
        # TODO: Contact activate device and start buzzing
        # TODO: If declined say so
        # TODO: Begin server and conntect to it, tell other device to connect to it and start call, set calling var to True

    @intent_file_handler('end.call.intent')
    def handle_communications(self, message):
        self.end_call()

    def end_call(self):
        # Check that we are calling someone
        if self.calling:
            # TODO: Stop Murmur call
            # TODO: stop server
            # TODO: end nicely, set self.calling to False
            # TODO: Don't say anything.
            pass
        else:
            return

    def stop(self):
        if self.calling:
            self.end_call()
            return True
        else:
            return False


def create_skill():
    return Communications()
