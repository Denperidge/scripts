from os import chdir, path, name
from subprocess import run

"""
If you're like me and postponed setting up ssh keys for way too long
and now you have a bunch of servers to do it with, here you go!

Credit where credit is due!
SSH setup tutorial: https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys-2

"""

prompt_instructions = "leave empty to exit this script!"
def prompt(prompt_text):
    # Add the exit instructions to the end of the prompt
    if ")" in prompt_text:  # If possible, add it into () brackets
        prompt_text = prompt_text.replace(")", ", {})".format(prompt_instructions))

    elif ":" in prompt_text:  # If there's no brackets, add it before the :
        # rstrip to ensure there's no double whitespace after :
        prompt_text = prompt_text.rstrip().replace(":", " ({}): ".format(prompt_instructions))

    else:
        prompt_text = prompt_text.rstrip() + " ({}): ".format(prompt_instructions)

    
    user_input = input(prompt_text)
    if (user_input.strip() != ""):
        return user_input.strip()
    else:
        exit(0)


# Change path to .ssh folder
chdir(path.expanduser("~") + "/.ssh")  # Also works on Windows, cool stuff

# Use of while True is okay here, considering the prompt function will be used for exiting
while True:
    # Get hostname and username

    username_and_hostmane = prompt("Type your ssh command here (f.e. login@server.com): ").split("@")
    username = username_and_hostmane[0]
    hostname = username_and_hostmane[1]

    nickname = prompt("Give this server a nickname (for example, FTP server): ")
    id_rsa_name = "id_rsa_" + nickname

    run('ssh-keygen -t rsa -f "id_rsa_"' + nickname)

    with open(id_rsa_name + ".pub", "r") as id_rsa_file:
        id_rsa_content = id_rsa_file.read()
    run('ssh {0} "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo "{1}" >> ~/.ssh/authorized_keys'.format("@".join(username_and_hostmane), id_rsa_content))
    
        
    comment = "SSH to {username_and_hostname}".format(username_and_hostname="@".join(username_and_hostmane))

    config_append = (
        "\n\n# {comment}"
        "\nHost {hostname}"
        "\n    User {username}"
        "\n    IdentityFile ~/.ssh/{id_rsa_name}"
    ).format(comment=comment, hostname=hostname, username=username, nickname=nickname, id_rsa_name=id_rsa_name)

    with open("config", "r") as config:
        add_config = comment not in config.read()
            

    if add_config:
        with open("config", "a+") as config:
            config.write(config_append)
        print("Config r")
    else:
        print("Entry already found in ~/.ssh/config")
    