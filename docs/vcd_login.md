```
Usage: vcd login [OPTIONS] host organization user

  Login to vCloud Director

      Login to a vCloud Director service.
  
      Examples
          vcd login mysp.com org1 usr1
              Login to host 'mysp.com'.
  
          vcd login test.mysp.com org1 usr1 -i -w
              Login to a host with self-signed SSL certificate.
  
          vcd login mysp.com org1 usr1 --use-browser-session
              Login using active session from browser.
  
          vcd login session list chrome
              List active session ids from browser.
  
          vcd login mysp.com org1 usr1 \
              --session-id ee968665bf3412d581bbc6192508eec4
              Login using active session id.
  
      Environment Variables
          VCD_PASSWORD
              If this environment variable is set, the command will use its value
              as the password to login and will not ask for one. The --password
              option has precedence over the environment variable.



Options:
  -p, --password <password>       Password
  -V, --version [5.5|5.6|6.0|13.0|17.0|20.0|21.0|22.0|23.0|24.0|25.0|26.0|27.0|28.0|29.0]
                                  API version
  -s, --verify-ssl-certs / -i, --no-verify-ssl-certs
                                  Verify SSL certificates
  -w, --disable-warnings          Do not display warnings when not verifying
                                  SSL certificates
  -v, --vdc TEXT                  virtual datacenter
  -d, --session-id TEXT           session id
  -b, --use-browser-session       Use browser session
  -h, --help                      Show this message and exit.

```
