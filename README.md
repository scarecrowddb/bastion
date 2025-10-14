# DevEnv for Work

Initial Installation:

```bash
apt update
apt upgrade -y
apt install software-properties-common -y
add-apt-repository --yes --update ppa:ansible/ansible
apt install ansible git -y
cd ~
git clone https://gitlab.octoengine.com/ansible/bastion.git
```

Update the password_file (Bitwarden: `bastion 10.212.212.20`)
```bash
nano /etc/ansible/password_file
```

Execute the Playbook
```bash
ansible-playbook playbook.yml --vault-password-file /etc/ansible/password_file
```

Encrypt Passwords:
```
ansible-vault encrypt_string --vault-password-file /etc/ansible/password_file --stdin-name 'password' --encrypt-vault-id default
```

Reset Ansible PAT in GitLab Here:  https://gitlab.octoengine.com/groups/ansible/-/settings/access_tokens


Don't forget to install Tailscale!
