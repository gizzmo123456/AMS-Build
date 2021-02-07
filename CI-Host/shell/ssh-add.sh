#!/usr/bin/expect -f

lassign $argv path pass

spawn ssh-add $a

expect "Enter passphrase for $path"

send -- "$pass\n"

send_user "done"