# Discord Bot Permissions Required

## Essential Permissions

The Global Chat Rooms bot requires the following Discord permissions to function properly:

### Text Permissions
- **Read Messages** - Required to see messages in channels
- **Send Messages** - Required to send cross-server messages and responses
- **Embed Links** - Required for rich embed responses (room lists, settings, help)
- **Read Message History** - Required to fetch messages for editing and reactions
- **Add Reactions** - Required for interactive permission setup system
- **Use External Emojis** - Optional but enhances user experience

### General Permissions
- **View Channels** - Required to access channels the bot is added to

## Permission Breakdown by Feature

### Core Chat Functionality
- **Read Messages**: To monitor messages in subscribed channels
- **Send Messages**: To broadcast messages across servers
- **Read Message History**: To access message content for cross-server relay

### Interactive Permission System
- **Add Reactions**: For the emoji-based permission configuration during room setup
- **Embed Links**: For rich permission setup interfaces and help messages

### Room Management
- **Send Messages**: For command responses and room management feedback
- **Embed Links**: For room lists, settings displays, and status messages

## Permissions NOT Required

The bot **does not** need these permissions (unlike many other Discord bots):

❌ **Administrator** - Not needed, we use minimal permissions
❌ **Manage Channels** - Bot only checks if *users* have this permission
❌ **Manage Messages** - Bot doesn't delete or edit user messages
❌ **Manage Roles** - No role management functionality
❌ **Manage Server** - No server-wide management needed
❌ **Connect/Speak** - No voice functionality
❌ **Manage Webhooks** - No webhook usage
❌ **Mention Everyone** - Bot doesn't ping @everyone/@here

## Permission Value

The minimal permission integer value for this bot is: **412885812288**

This includes:
- View Channels (1024)
- Send Messages (2048) 
- Embed Links (16384)
- Read Message History (65536)
- Add Reactions (64)
- Use External Emojis (262144)

## Security Benefits

### Minimal Attack Surface
- No dangerous permissions like "Manage Messages" or "Administrator"
- Cannot delete user content or modify server settings
- Limited to basic messaging and reaction functionality

### User Privacy
- Cannot read messages in channels it's not explicitly invited to
- No access to user voice channels or private channels
- Cannot modify user roles or permissions

### Server Safety
- Cannot kick/ban users or modify server structure
- Cannot create/delete channels or modify channel permissions
- Cannot manage webhooks or external integrations

## Setup Instructions

### For Server Administrators

1. **Invite the bot** with the minimal permissions listed above
2. **No additional setup required** - the bot works in any channel it can access
3. **Grant "Manage Channels" permission** to users who should create/manage rooms (this is a user permission, not a bot permission)

### Bot Invite Link Format
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=412885812288&scope=bot%20applications.commands
```

### Permission Verification

You can verify the bot has correct permissions by:
1. Right-clicking the bot in your server
2. Checking "Roles" section
3. Ensuring it has the permissions listed above

## Troubleshooting

### Bot Can't Send Messages
- Ensure bot has "Send Messages" permission in target channel
- Check channel-specific permission overrides

### Interactive Setup Not Working
- Ensure bot has "Add Reactions" permission
- Verify "Embed Links" permission is enabled

### Commands Not Responding
- Check if bot can "Read Messages" in the channel
- Verify bot role is above any restrictive roles

## Migration from Previous Versions

If upgrading from a music bot version that had Administrator permissions:

1. **Remove Administrator permission** from the bot role
2. **Grant only the minimal permissions** listed above
3. **No functionality will be lost** - all global chat features remain intact
4. **Improved security** with reduced permission footprint

## Support

For permission-related issues:
- Verify permissions using the checklist above
- Check Discord's audit log for permission changes
- Contact support with your server ID and permission screenshots