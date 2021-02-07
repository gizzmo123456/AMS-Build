#!/usr/bin/expect -f

lassign $argv path pass

spawn ssh-add $pass

expect "Enter passphrase for $path"

send -- "$pass\n"

send_user "done"