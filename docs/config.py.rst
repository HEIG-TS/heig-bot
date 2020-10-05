config.json
===========

`config.json.sample` is a template for `config.json`


- **database_directory**:
    Directory where is saved all dynamic
    information about bot. Including user password for GAPS.
- **bot_token**:
    Telegram token for access to telegram API.
- **debug**:
    Level of debug

    - **0**: no debug
    - **1**: debug on console only
    - **2**: debug on console and send to `group/debug`
    - **3**: same as **2** and send to user.
- **debug_send**:
    Level of debug for send message. Value between 0
    and 2, with same meaning of `debug`
- **admin_exec**:
    Enable/disable shell exec command for admins

    - **off**: exec command is disable
    - **on**: exec command is enable
- **group**:
    Is a map of group name and id list.
- **group/admin**:
    String list of user telegram id for
    administrators
- **group/log**:
    String list of chat telegram id for
    logging (start message)
- **group/debug**:
    String list of chat telegram id for
    debug