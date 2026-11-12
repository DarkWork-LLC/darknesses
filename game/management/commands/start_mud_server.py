"""
Django management command to start the MUD Telnet server.
Also checks if the port is already in use and warns the user.
"""
import os
import sys
import socket
import django
import asyncio
from django.core.management.base import BaseCommand


def check_port(host, port):
    """Check if a port is already in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return False  # Port is available
    except socket.error as e:
        sock.close()
        return True  # Port is in use


class Command(BaseCommand):
    help = 'Start the MUD Telnet server for MUD client connections'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default='0.0.0.0',
            help='Host to bind the server to (default: 0.0.0.0)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=4000,
            help='Port to listen on (default: 4000)'
        )
    
    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        
        # Check if port is already in use
        if check_port(host, port):
            self.stdout.write(
                self.style.WARNING(f'Port {port} on {host} is already in use!')
            )
            self.stdout.write(
                self.style.WARNING('The MUD server may fail to start.')
            )
            self.stdout.write(
                self.style.WARNING('Make sure no other service is using this port.')
            )
            # Ask user if they want to proceed anyway
            self.stdout.write("")
            proceed = input('Do you want to proceed anyway? (y/n): ')
            if proceed.lower() != 'y':
                self.stdout.write(
                    self.style.SUCCESS('MUD server startup cancelled.')
                )
                return
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting MUD server on {host}:{port}...')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Connect using: telnet {host} {port}')
        )
        self.stdout.write(
            self.style.WARNING('Press Ctrl+C to stop the server.\n')
        )
        
        # Import and run the MUD server
        from game.mud_server import run_mud_server
        
        try:
            asyncio.run(run_mud_server(host, port))
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('\nMUD server stopped.')
            )
