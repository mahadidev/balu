import { Metadata } from 'next'
import { Column, Heading, Text, Badge, Row } from "@once-ui-system/core"

export const metadata: Metadata = {
  title: 'Terms of Service - Balu Discord Bot',
  description: 'Terms of Service for Balu Discord Bot outlining usage guidelines, responsibilities, and service limitations.',
}

export default function Terms() {
  return (
    <Column maxWidth="l" gap="xl" paddingY="24" paddingX="16">
      <Column gap="16">
        <Heading as="h1" variant="display-strong-l">
          Terms of Service
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
          <Heading as="h2" variant="heading-strong-l">1. Acceptance of Terms</Heading>
          <Text variant="body-default-m">
            By adding Balu Discord Bot ("Balu," "the bot," "we," "our," or "us") to your Discord server or using any of its features, you ("user," "you," or "your") agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, please do not use Balu.
          </Text>
        </Column>

        {/* Description of Service */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">2. Description of Service</Heading>
          <Text variant="body-default-m">
            Balu is a Discord bot that provides the following services:
          </Text>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• <strong>Music Streaming:</strong> YouTube music playback, queue management, and playlist features</Text>
            <Text variant="body-default-m">• <strong>Voice Management:</strong> Tools for managing voice channels and moving users</Text>
            <Text variant="body-default-m">• <strong>Channel Management:</strong> Creating, organizing, and managing server channels</Text>
            <Text variant="body-default-m">• <strong>Cross-Server Chat:</strong> Global chat rooms connecting multiple Discord servers</Text>
            <Text variant="body-default-m">• <strong>Server Administration:</strong> Various administrative and moderation tools</Text>
          </Column>
        </Column>

        {/* User Responsibilities */}
        <Column gap="16">
          <Heading as="h2" variant="heading-strong-l">3. User Responsibilities</Heading>
          
          <Column gap="12">
            <Heading as="h3" variant="heading-strong-m">3.1 Acceptable Use</Heading>
            <Text variant="body-default-m">You agree to use Balu only for lawful purposes and in accordance with these Terms. You will not:</Text>
            <Column gap="8" paddingLeft="16">
              <Text variant="body-default-m">• Use the bot to stream copyrighted content without proper authorization</Text>
              <Text variant="body-default-m">• Attempt to exploit, hack, or reverse engineer the bot's functionality</Text>
              <Text variant="body-default-m">• Use the bot to harass, abuse, or harm other users</Text>
              <Text variant="body-default-m">• Spam commands or attempt to overwhelm the bot's systems</Text>
              <Text variant="body-default-m">• Use the bot for commercial purposes without written permission</Text>
              <Text variant="body-default-m">• Share inappropriate, offensive, or illegal content through the bot</Text>
            </Column>
          </Column>

          <Column gap="12">
            <Heading as="h3" variant="heading-strong-m">3.2 Server Administrator Responsibilities</Heading>
            <Column gap="8" paddingLeft="16">
              <Text variant="body-default-m">• Ensure all server members understand and follow these Terms</Text>
              <Text variant="body-default-m">• Monitor the bot's usage in your server and report any violations</Text>
              <Text variant="body-default-m">• Respect Discord's Terms of Service and Community Guidelines</Text>
              <Text variant="body-default-m">• Configure bot permissions appropriately for your server's needs</Text>
            </Column>
          </Column>
        </Column>

        {/* Bot Limitations */}
        <Column gap="16">
          <Heading as="h2" variant="heading-strong-l">4. Service Limitations and Availability</Heading>
          
          <Column gap="12">
            <Heading as="h3" variant="heading-strong-m">4.1 Service Availability</Heading>
            <Column gap="8" paddingLeft="16">
              <Text variant="body-default-m">• Balu is provided "as is" without guarantees of uptime or availability</Text>
              <Text variant="body-default-m">• We may temporarily suspend service for maintenance, updates, or technical issues</Text>
              <Text variant="body-default-m">• Music streaming depends on external services (YouTube) which may experience outages</Text>
              <Text variant="body-default-m">• We do not guarantee continuous, uninterrupted service</Text>
            </Column>
          </Column>

          <Column gap="12">
            <Heading as="h3" variant="heading-strong-m">4.2 Content and Copyright</Heading>
            <Column gap="8" paddingLeft="16">
              <Text variant="body-default-m">• Balu streams content from YouTube - all content rights belong to original creators</Text>
              <Text variant="body-default-m">• Users are responsible for ensuring they have rights to request and play specific content</Text>
              <Text variant="body-default-m">• We do not store, cache, or redistribute copyrighted audio content</Text>
              <Text variant="body-default-m">• Music features are for personal, non-commercial use only</Text>
            </Column>
          </Column>
        </Column>

        {/* Data and Privacy */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">5. Data Collection and Privacy</Heading>
          <Text variant="body-default-m">
            Our data collection and privacy practices are detailed in our Privacy Policy. By using Balu, you consent to:
          </Text>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• Collection of Discord User IDs and Server IDs for bot functionality</Text>
            <Text variant="body-default-m">• Temporary storage of music queues and command history</Text>
            <Text variant="body-default-m">• Processing of voice channel data for music streaming</Text>
            <Text variant="body-default-m">• Automatic deletion of data when the bot is removed from your server</Text>
          </Column>
        </Column>

        {/* Intellectual Property */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">6. Intellectual Property</Heading>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• Balu's code, design, and functionality are proprietary</Text>
            <Text variant="body-default-m">• You may not copy, modify, or redistribute the bot's code</Text>
            <Text variant="body-default-m">• All trademarks and service marks remain the property of their respective owners</Text>
            <Text variant="body-default-m">• Users retain rights to their own content shared through the bot</Text>
          </Column>
        </Column>

        {/* Disclaimers */}
        <Column gap="16">
          <Heading as="h2" variant="heading-strong-l">7. Disclaimers and Limitations</Heading>
          
          <Row gap="16" wrap s={{ direction: 'column' }}>
            <Column
              flex={1}
              gap="12"
              padding="16"
              background="warning-alpha-weak"
              radius="m"
            >
              <Text variant="heading-strong-s">⚠️ Service Disclaimers</Text>
              <Column gap="4">
                <Text variant="body-default-s">• No warranty of continuous operation</Text>
                <Text variant="body-default-s">• No guarantee of data preservation</Text>
                <Text variant="body-default-s">• External service dependencies may fail</Text>
                <Text variant="body-default-s">• Features may change without notice</Text>
              </Column>
            </Column>

            <Column
              flex={1}
              gap="12"
              padding="16"
              background="neutral-alpha-weak"
              radius="m"
            >
              <Text variant="heading-strong-s">🛡️ Liability Limitations</Text>
              <Column gap="4">
                <Text variant="body-default-s">• Not liable for server disruptions</Text>
                <Text variant="body-default-s">• Not responsible for user-generated content</Text>
                <Text variant="body-default-s">• Not liable for third-party service failures</Text>
                <Text variant="body-default-s">• Limited liability for any damages</Text>
              </Column>
            </Column>
          </Row>
        </Column>

        {/* Termination */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">8. Termination</Heading>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• You may remove Balu from your server at any time</Text>
            <Text variant="body-default-m">• We may terminate service for violations of these Terms</Text>
            <Text variant="body-default-m">• We may discontinue the bot service with reasonable notice</Text>
            <Text variant="body-default-m">• Upon termination, all associated data will be deleted</Text>
          </Column>
        </Column>

        {/* Discord Terms */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">9. Discord Terms Compliance</Heading>
          <Text variant="body-default-m">
            By using Balu, you agree that your use must comply with:
          </Text>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• Discord's Terms of Service</Text>
            <Text variant="body-default-m">• Discord's Community Guidelines</Text>
            <Text variant="body-default-m">• Discord's Developer Terms of Service</Text>
            <Text variant="body-default-m">• All applicable local, state, and federal laws</Text>
          </Column>
        </Column>

        {/* Modifications */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">10. Modifications to Terms</Heading>
          <Text variant="body-default-m">
            We reserve the right to modify these Terms at any time. Changes will be effective immediately upon posting on our website. Continued use of Balu after changes constitutes acceptance of the new Terms. We recommend reviewing these Terms periodically.
          </Text>
        </Column>

        {/* Governing Law */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">11. Governing Law</Heading>
          <Text variant="body-default-m">
            These Terms shall be governed by and construed in accordance with applicable laws. Any disputes arising from these Terms or use of Balu shall be resolved through appropriate legal channels in the jurisdiction where the service is provided.
          </Text>
        </Column>

        {/* Contact Information */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">12. Contact Information</Heading>
          <Text variant="body-default-m">
            If you have questions about these Terms of Service, please contact us:
          </Text>
          <Column gap="8" paddingLeft="16">
            <Text variant="body-default-m">• <strong>Discord:</strong> Contact server administrators where Balu is installed</Text>
            <Text variant="body-default-m">• <strong>GitHub:</strong> Open an issue on our GitHub repository</Text>
            <Text variant="body-default-m">• <strong>Server Support:</strong> Use support channels in Discord servers where Balu is active</Text>
          </Column>
        </Column>

        {/* Severability */}
        <Column gap="12">
          <Heading as="h2" variant="heading-strong-l">13. Severability</Heading>
          <Text variant="body-default-m">
            If any provision of these Terms is found to be unenforceable or invalid, that provision will be limited or eliminated to the minimum extent necessary so that these Terms will otherwise remain in full force and effect.
          </Text>
        </Column>

        {/* Footer */}
        <Column gap="8" paddingTop="16" borderTop="neutral-alpha-weak" borderStyle="solid">
          <Badge
            background="brand-alpha-weak"
            onBackground="brand-strong"
            paddingX="12"
            paddingY="4"
          >
            📋 By using Balu Discord Bot, you acknowledge that you have read, understood, and agree to these Terms of Service.
          </Badge>
          
          <Text variant="body-default-s" onBackground="neutral-weak">
            These Terms of Service were last updated on November 7, 2024. For questions about privacy, please see our Privacy Policy.
          </Text>
        </Column>
      </Column>
    </Column>
  )
}