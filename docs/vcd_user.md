```
Usage: vcd user [OPTIONS] COMMAND [ARGS]...

  Work with users in current organization.

      Examples
          vcd user create my-user my-password role-name
             create user in the current organization with my-user password
             and role-name.
  
          vcd user create 'my user' 'my password' 'role name'
             create user in the current organization with 'my user'
             'my password' and 'role name'.
  
          vcd user delete 'my user'
             deletes user with username "my user" from the current organization.
             Will also delete vApps owned by the user. If user has running vApps,
             this command will result in error.
  
          vcd user update 'my user' --enable
             update user in the current organization, e.g enable the user



Options:
  -h, --help  Show this message and exit.

Commands:
  create  create user in current organization
  delete  delete an user in current organization
  update  update an user in current organizaton

```
