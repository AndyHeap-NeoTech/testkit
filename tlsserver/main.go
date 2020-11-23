package main

import (
	"crypto/tls"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"time"
)

func exitWithError(err error) {
	fmt.Println(err)
	os.Exit(-1)
}

var expectedHandshake = []byte{0x60, 0x60, 0xb0, 0x17}

// Do not print anything on stdout until listening!
func main() {
	var (
		address        string
		network        string
		certPath       string
		keyPath        string
		minTlsMinorVer int
		maxTlsMinorVer int
		disableTls     bool
		listener       net.Listener
		err            error
	)
	flag.BoolVar(&disableTls, "disableTls", false, "Disable TLS")
	flag.StringVar(&address, "bind", "0.0.0.0:6666", "Address to bind to")
	flag.StringVar(&network, "network", "tcp", "Network type to bind to")
	flag.StringVar(&certPath, "cert", "", "Path to server certificate")
	flag.StringVar(&keyPath, "key", "", "Path to server private key")
	flag.IntVar(&minTlsMinorVer, "minTls", 0, "Minimum TLS version, minor part")
	flag.IntVar(&maxTlsMinorVer, "maxTls", 2, "Maximum TLS version, minor part")
	flag.Parse()

	if network == "unix" {
		// Need to remove UDS file before continuing
		// Ignore error, if the file didn't exist it is fine or if it did
		// exist but we failed to remove it we will get an error upon listen.
		os.Remove(address)
	}

	if !disableTls {
		cert, err := tls.LoadX509KeyPair(certPath, keyPath)
		if err != nil {
			exitWithError(err)
		}

		config := tls.Config{
			GetCertificate: func(hello *tls.ClientHelloInfo) (*tls.Certificate, error) {
				// TODO: Set cert.OCSPStaple
				return &cert, nil
			},
			MinVersion: 0x0300 | uint16(minTlsMinorVer+1),
			MaxVersion: 0x0300 | uint16(maxTlsMinorVer+1),
		}
		listener, err = tls.Listen(network, address, &config)
		if err != nil {
			exitWithError(err)
		}
		fmt.Printf("TLS, listening on %s:%s with cert %s\n", network, address, certPath)
	} else {
		listener, err = net.Listen(network, address)
		if err != nil {
			exitWithError(err)
		}
		fmt.Printf("Listening on non-TLS %s:%s\n", network, address)
	}
	defer listener.Close()

	conn, err := listener.Accept()
	if err != nil {
		exitWithError(err)
	}
	// Deadline needed for dotnet, seems to stick to the socket even when TLS handshake failed.
	// Deadline is a good thing anyway...
	conn.SetReadDeadline(time.Now().Add(1 * time.Second))
	fmt.Printf("TLS, client connected from %s, waiting for Bolt handshake\n", conn.RemoteAddr())

	handshake := make([]byte, 4*5)
	_, err = io.ReadFull(conn, handshake)
	if err != nil {
		fmt.Println("Failed to receive Bolt handshake")
		exitWithError(err)
	}
	conn.Close()

	// Just check the signature
	for i, x := range expectedHandshake {
		if x != handshake[i] {
			exitWithError(errors.New("Bad Bolt handshake"))
		}
	}

	fmt.Println("Client connected with correct Bolt handshake")
}
