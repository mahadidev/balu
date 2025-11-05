import { Mailchimp } from "@/components";
import { Posts } from "@/components/blog/Posts";
import { Projects } from "@/components/work/Projects";
import { about, baseURL, home, person, routes } from "@/resources";
import {
  Avatar,
  Badge,
  Button,
  Column,
  Heading,
  Line,
  Meta,
  RevealFx,
  Row,
  Schema,
  Text,
} from "@once-ui-system/core";

export async function generateMetadata() {
  return Meta.generate({
    title: home.title,
    description: home.description,
    baseURL: baseURL,
    path: home.path,
    image: home.image,
  });
}

export default function Home() {
  return (
    <Column maxWidth="m" gap="xl" paddingY="12" horizontal="center">
      <Schema
        as="webPage"
        baseURL={baseURL}
        path={home.path}
        title={home.title}
        description={home.description}
        image={`/api/og/generate?title=${encodeURIComponent(home.title)}`}
        author={{
          name: person.name,
          url: `${baseURL}${about.path}`,
          image: `${baseURL}${person.avatar}`,
        }}
      />
      <Column fillWidth horizontal="center" gap="m">
        <Column maxWidth="s" horizontal="center" align="center">
          {home.featured.display && (
            <RevealFx
              fillWidth
              horizontal="center"
              paddingTop="16"
              paddingBottom="32"
              paddingLeft="12"
            >
              <Badge
                background="brand-alpha-weak"
                paddingX="12"
                paddingY="4"
                onBackground="neutral-strong"
                textVariant="label-default-s"
                arrow={false}
                href={home.featured.href}
              >
                <Row paddingY="2">{home.featured.title}</Row>
              </Badge>
            </RevealFx>
          )}
          <RevealFx translateY="4" fillWidth horizontal="center" paddingBottom="16">
            <Heading wrap="balance" variant="display-strong-l">
              {home.headline}
            </Heading>
          </RevealFx>
          <RevealFx translateY="8" delay={0.2} fillWidth horizontal="center" paddingBottom="32">
            <Text wrap="balance" onBackground="neutral-weak" variant="heading-default-xl">
              {home.subline}
            </Text>
          </RevealFx>
          <RevealFx paddingTop="12" delay={0.4} horizontal="center" paddingLeft="12">
            <Button
              id="about"
              data-border="rounded"
              href={about.path}
              variant="secondary"
              size="m"
              weight="default"
              arrowIcon
            >
              <Row gap="8" vertical="center" paddingRight="4">
                {about.avatar.display && (
                  <Avatar
                    marginRight="8"
                    style={{ marginLeft: "-0.75rem" }}
                    src={person.avatar}
                    size="m"
                  />
                )}
                {about.title}
              </Row>
            </Button>
          </RevealFx>
        </Column>
      </Column>
      
      {/* Commands Section */}
      <RevealFx translateY="12" delay={0.6}>
        <Column fillWidth gap="40" marginBottom="40">
          <Row fillWidth gap="24" wrap s={{ direction: "column" }} horizontal="center">
            {/* Music Commands Card */}
            <Column flex={1} gap="24" padding="24" background="surface" radius="l" border="neutral-alpha-weak" borderStyle="solid">
              <Row gap="12" vertical="center">
                <Text variant="display-strong-xs">🎵</Text>
                <Heading as="h3" variant="heading-strong-m">Music Player</Heading>
              </Row>
              <Column gap="12">
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">/play</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">Start playing music</Text>
                </Row>
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">!skip</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">Skip current song</Text>
                </Row>
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">!queue</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">View music queue</Text>
                </Row>
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">!repeat</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">Toggle repeat mode</Text>
                </Row>
              </Column>
            </Column>

            {/* Global Chat Commands Card */}
            <Column flex={1} gap="24" padding="24" background="surface" radius="l" border="neutral-alpha-weak" borderStyle="solid">
              <Row gap="12" vertical="center">
                <Text variant="display-strong-xs">🌐</Text>
                <Heading as="h3" variant="heading-strong-m">Global Chat</Heading>
              </Row>
              <Column gap="12">
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">!chat_subscribe</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">Join the network</Text>
                </Row>
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">!chat_create</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">Create new chat</Text>
                </Row>
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">!chat_status</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">Check network status</Text>
                </Row>
              </Column>
            </Column>

            {/* Voice Management Commands Card */}
            <Column flex={1} gap="24" padding="24" background="surface" radius="l" border="neutral-alpha-weak" borderStyle="solid">
              <Row gap="12" vertical="center">
                <Text variant="display-strong-xs">🎤</Text>
                <Heading as="h3" variant="heading-strong-m">Voice Tools</Heading>
              </Row>
              <Column gap="12">
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">/moveall</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">Move all users</Text>
                </Row>
                <Row gap="16" vertical="center">
                  <Badge background="brand-alpha-weak" onBackground="brand-strong" textVariant="code-default-s" paddingX="8" paddingY="4">!channels</Badge>
                  <Text variant="body-default-s" onBackground="neutral-weak">List voice channels</Text>
                </Row>
              </Column>
            </Column>
          </Row>
          
          <Column horizontal="center" paddingTop="24">
            <Button
              href="/work"
              variant="tertiary"
              size="m"
              arrowIcon
            >
              View all commands
            </Button>
          </Column>
        </Column>
      </RevealFx>
      
      <RevealFx translateY="16" delay={0.8}>
        <Projects range={[1, 1]} />
      </RevealFx>
      <Projects range={[2]} />
      <Mailchimp />
    </Column>
  );
}
