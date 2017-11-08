```
Usage: vcd user create [OPTIONS] <user_name> <password> <role-name>

Options:
  -e, --email [email]             User's email address.
  -f, --full-name [full_name]     Full name of the user.
  -D, --description [description]
                                  description.
  -t, --telephone [telephone]     User's telephone number.
  -i, --im [im]                   User's im address.
  -E, --enabled                   Enable user
  --alert-enabled                 Enable alerts
  --alert-email [alert_email]     Alert email address
  --alert-email-prefix [alert_email_prefix]
                                  String to prepend to the alert message
                                  subject line
  --external                      Indicates if user is imported from an
                                  external source
  --default-cached                Indicates if user should be cached
  -g, --group-role                Indicates if the user has a group role
  -s, --stored-vm-quota [stored_vm_quota]
                                  Quota of vApps that this user can store
  -d, --deployed-vm-quota [deployed_vm_quota]
                                  Quota of vApps that this user can deploy
                                  concurrently
  -h, --help                      Show this message and exit.

```
