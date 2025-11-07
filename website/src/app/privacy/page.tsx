import { Metadata } from 'next'
import { Column, Heading, Text, Badge, Row } from "@once-ui-system/core"

export const metadata: Metadata = {
  title: 'Privacy Policy - Balu Discord Bot',
  description: 'Privacy policy for Balu Discord Bot explaining data collection, usage, and user rights.',
}

export default function Privacy() {
  return (
    <Column maxWidth="l" gap="xl" paddingY="24" paddingX="16">
      <Column gap="16">
        <Heading as="h1" variant="display-strong-l">
          Privacy Policy
        </Heading>
        
        <Column gap="8">
          <Text variant="body-default-m" onBackground="neutral-weak">
            <strong>Effective Date:</strong> November 7, 2024
          </Text>
          <Text variant="body-default-m" onBackground="neutral-weak">
            <strong>Last Updated:</strong> November 7, 2024
          </Text>
        </Column>
      </Column>

      <Column gap="24">
        {/* Introduction */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">1. Introduction</Heading>
          <Text variant="body-default-m">
            This Privacy Policy explains how Balu Discord Bot ("we," "our," or "the bot") collects, uses, and protects information when you use our Discord bot services. By using Balu, you agree to the collection and use of information in accordance with this policy.
          </Text>
        </Column>

        {/* Information We Collect */}
        <Column gap="16">
          <Heading as="h2" variant="heading-strong-l">2. Information We Collect</Heading>
          
          <Column gap="12">
            <Heading as="h3" variant="heading-strong-m">2.1 Automatically Collected Information</Heading>
            <Column gap="8" paddingLeft="16">
              <Text variant="body-default-m">• <strong>Discord User IDs:</strong> We collect Discord user IDs to track music requests and queue management</Text>
              <Text variant="body-default-m">• <strong>Discord Server IDs:</strong> We collect server (guild) IDs to maintain separate bot configurations per server</Text>
              <Text variant="body-default-m">• <strong>Voice Channel Information:</strong> We access voice channel data to provide music playback services</Text>
              <Text variant="body-default-m">• <strong>Command Usage:</strong> We log bot commands for functionality and debugging purposes</Text>
            </Column>
          </Column>

          <Column gap="12">
            <Heading as="h3" variant="heading-strong-m">2.2 Information We Do NOT Collect</Heading>
            <Column gap="8" paddingLeft="16">
              <Text variant="body-default-m">• Message content (except direct bot commands)</Text>
              <Text variant="body-default-m">• Personal conversations or private messages</Text>
              <Text variant="body-default-m">• Email addresses or personal contact information</Text>
              <Text variant="body-default-m">• Payment or financial information</Text>
              <Text variant="body-default-m">• Voice recordings or audio content</Text>
            </Column>
          </Column>
        </Column>

        {/* How We Use Information */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">3. How We Use Your Information</Heading>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• <strong>Music Services:</strong> To provide music playback, queue management, and related features</Text>
            <Text variant="body-default-m">• <strong>Voice Management:</strong> To join and manage voice channels for music streaming</Text>
            <Text variant="body-default-m">• <strong>Channel Management:</strong> To create, modify, and manage channels as requested by authorized users</Text>
            <Text variant="body-default-m">• <strong>Chat Moderation:</strong> To provide chat management and moderation features</Text>
            <Text variant="body-default-m">• <strong>Bot Functionality:</strong> To maintain bot operations, troubleshoot issues, and improve services</Text>
            <Text variant="body-default-m">• <strong>User Experience:</strong> To personalize and enhance your interaction with the bot</Text>
          </Column>
        </Column>

        {/* Data Storage */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">4. Data Storage and Security</Heading>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• <strong>Local Storage:</strong> Most data is stored temporarily in local databases and cleared regularly</Text>
            <Text variant="body-default-m">• <strong>No Cloud Storage:</strong> We do not store personal data in external cloud services</Text>
            <Text variant="body-default-m">• <strong>Automatic Deletion:</strong> Music queues and temporary data are automatically cleared when the bot restarts</Text>
            <Text variant="body-default-m">• <strong>Security Measures:</strong> We implement appropriate technical safeguards to protect collected data</Text>
          </Column>
        </Column>

        {/* Third Party Services */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">5. Third-Party Services</Heading>
          <Text variant="body-default-m">
            Balu integrates with the following third-party services:
          </Text>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• <strong>YouTube:</strong> For music streaming (subject to YouTube's Terms of Service and Privacy Policy)</Text>
            <Text variant="body-default-m">• <strong>Discord API:</strong> For all bot functionality (subject to Discord's Terms of Service and Privacy Policy)</Text>
          </Column>
          <Text variant="body-default-m">
            We do not share your personal information with these services beyond what is necessary for bot functionality.
          </Text>
        </Column>

        {/* User Rights */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">6. Your Rights and Choices</Heading>
          <Text variant="body-default-m">You have the right to:</Text>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• <strong>Remove the Bot:</strong> You can remove Balu from your server at any time, which will delete all associated data</Text>
            <Text variant="body-default-m">• <strong>Data Deletion:</strong> Contact us to request deletion of any stored data related to your server or user ID</Text>
            <Text variant="body-default-m">• <strong>Access Information:</strong> Request information about what data we have collected about you</Text>
            <Text variant="body-default-m">• <strong>Limit Usage:</strong> Restrict the bot's permissions in your Discord server settings</Text>
          </Column>
        </Column>

        {/* Permissions */}
        <Column gap="16">
          <Heading as="h2" variant="heading-strong-l">7. Permissions Explanation</Heading>
          <Text variant="body-default-m">
            <strong>Why We Need Administrator Permissions:</strong>
          </Text>
          <Text variant="body-default-m">
            Balu requests Administrator permissions to provide comprehensive server management features:
          </Text>
          
          <Row gap="16" wrap s={{ direction: 'column' }}>
            <Column
              flex={1}
              gap="12"
              padding="16"
              background="accent-alpha-weak"
              radius="m"
            >
              <Text variant="heading-strong-s">🎵 Music Features</Text>
              <Column gap="4">
                <Text variant="body-default-s">• <strong>Connect to Voice Channels:</strong> Join any voice channel to play music</Text>
                <Text variant="body-default-s">• <strong>Speak in Voice Channels:</strong> Stream audio content</Text>
                <Text variant="body-default-s">• <strong>Use Voice Activity:</strong> Detect when to start/stop music</Text>
              </Column>
            </Column>

            <Column
              flex={1}
              gap="12"
              padding="16"
              background="brand-alpha-weak"
              radius="m"
            >
              <Text variant="heading-strong-s">💬 Chat Management</Text>
              <Column gap="4">
                <Text variant="body-default-s">• <strong>Send Messages:</strong> Respond to commands and provide feedback</Text>
                <Text variant="body-default-s">• <strong>Embed Links:</strong> Display rich music information and controls</Text>
                <Text variant="body-default-s">• <strong>Read Message History:</strong> Access commands and maintain context</Text>
                <Text variant="body-default-s">• <strong>Manage Messages:</strong> Clean up bot responses and moderate chat</Text>
              </Column>
            </Column>

            <Column
              flex={1}
              gap="12"
              padding="16"
              background="neutral-alpha-weak"
              radius="m"
            >
              <Text variant="heading-strong-s">🔧 Channel Management</Text>
              <Column gap="4">
                <Text variant="body-default-s">• <strong>Manage Channels:</strong> Create, modify, and organize server channels</Text>
                <Text variant="body-default-s">• <strong>View Channels:</strong> Access all channels for comprehensive management</Text>
                <Text variant="body-default-s">• <strong>Move Members:</strong> Relocate users between voice channels when needed</Text>
              </Column>
            </Column>
          </Row>

          <Badge
            background="warning-alpha-weak"
            onBackground="warning-strong"
            paddingX="12"
            paddingY="4"
          >
            Note: You can limit these permissions in your Discord server settings if you only want specific features.
          </Badge>
        </Column>

        {/* Data Retention */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">8. Data Retention</Heading>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• Music queue data is deleted when songs finish playing or the bot restarts</Text>
            <Text variant="body-default-m">• Channel management history is not permanently stored</Text>
            <Text variant="body-default-m">• User preferences are retained until the bot is removed from the server</Text>
            <Text variant="body-default-m">• Error logs may be kept for up to 30 days for debugging purposes</Text>
          </Column>
        </Column>

        {/* Children's Privacy */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">9. Children's Privacy</Heading>
          <Text variant="body-default-m">
            Balu is not intended for use by children under 13 years of age. We do not knowingly collect personal information from children under 13. If you believe we have collected information from a child under 13, please contact us immediately.
          </Text>
        </Column>

        {/* Changes */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">10. Changes to This Privacy Policy</Heading>
          <Text variant="body-default-m">
            We may update this Privacy Policy from time to time. We will notify users of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date. You are advised to review this Privacy Policy periodically for any changes.
          </Text>
        </Column>

        {/* Contact */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">11. Contact Us</Heading>
          <Text variant="body-default-m">
            If you have any questions about this Privacy Policy, please contact us:
          </Text>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• <strong>Discord:</strong> Contact server administrators where Balu is installed</Text>
            <Text variant="body-default-m">• <strong>GitHub:</strong> Open an issue on our GitHub repository</Text>
            <Text variant="body-default-m">• <strong>Server Support:</strong> Use the support channels in Discord servers where Balu is active</Text>
          </Column>
        </Column>

        {/* Footer */}
        <Column gap="8" paddingTop="16" borderTop="neutral-alpha-weak" borderStyle="solid">
          <Text variant="body-default-s" onBackground="neutral-weak">
            This privacy policy was last updated on November 7, 2024. By continuing to use Balu Discord Bot after any changes to this policy, you agree to the updated terms.
          </Text>
        </Column>
      </Column>
    </Column>
  )
}