```
Usage: vcd system amqp [OPTIONS] COMMAND [ARGS]...

  Manages AMQP settings in vCloud Director.

      Examples
          vcd system amqp info
              Get details of AMQP configuration.
  
          vcd -j system amqp info > amqp-config.json
              Save current AMQP configuration to file.
  
          vcd system amqp test amqp-config.json --password guest
              Test AMQP configuration.
  
          vcd system amqp set amqp-config.json --password guest
              Set AMQP configuration.
      

Options:
  -h, --help  Show this message and exit.

Commands:
  info  show AMQP settings
  set   configure AMQP settings
  test  test AMQP settings

```
