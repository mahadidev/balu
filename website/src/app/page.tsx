import { Mailchimp } from "@/components";
import { Projects } from "@/components/work/Projects";
import { about, baseURL, home, person, routes } from "@/resources";
import {
	Avatar,
	Badge,
	Button,
	Column,
	Heading,
	Icon,
	Line,
	Meta,
	RevealFx,
	Row,
	Schema,
	Text,
} from "@once-ui-system/core";
import Image from "next/image";

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
			{/* Hero Section */}
			<Column id="home" fillWidth horizontal="center" gap="m">
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
					<RevealFx
						translateY="4"
						fillWidth
						horizontal="center"
						paddingBottom="16"
					>
						<Heading wrap="balance" variant="display-strong-l">
							{home.headline}
						</Heading>
					</RevealFx>
					<RevealFx
						translateY="8"
						delay={0.2}
						fillWidth
						horizontal="center"
						paddingBottom="32"
					>
						<Text
							wrap="balance"
							onBackground="neutral-weak"
							variant="heading-default-xl"
						>
							{home.subline}
						</Text>
					</RevealFx>
					<RevealFx
						paddingTop="12"
						delay={0.4}
						horizontal="center"
						paddingLeft="12"
					>
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
								<Icon name="download" size="s" />
								{about.avatar.display && (
									<Avatar
										marginRight="8"
										style={{ marginLeft: '-0.75rem' }}
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
			<div style={{
				width: "100%"
			}} id="commands">
				<RevealFx translateY="12" delay={0.6}>
					<Column fillWidth gap="40">
						<Row
							fillWidth
							gap="24"
							wrap
							s={{ direction: 'column' }}
							horizontal="center"
						>
							{/* Music Commands Card */}
							<Column
								flex={1}
								gap="24"
								padding="24"
								background="surface"
								radius="l"
								border="neutral-alpha-weak"
								borderStyle="solid"
							>
								<Row gap="12" vertical="center">
									<Text variant="display-strong-xs">🎵</Text>
									<Heading as="h3" variant="heading-strong-m">
										Music Player
									</Heading>
								</Row>
								<Column gap="12">
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!play
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											Start playing music
										</Text>
									</Row>
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!skip
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											Skip current song
										</Text>
									</Row>
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!queue
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											View music queue
										</Text>
									</Row>
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!repeat
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											Toggle repeat mode
										</Text>
									</Row>
								</Column>
							</Column>

							{/* Cross Server Chat Commands Card */}
							<Column
								flex={1}
								gap="24"
								padding="24"
								background="surface"
								radius="l"
								border="neutral-alpha-weak"
								borderStyle="solid"
							>
								<Row gap="12" vertical="center">
									<Text variant="display-strong-xs">🌐</Text>
									<Heading as="h3" variant="heading-strong-m">
										Cross Server Chat
									</Heading>
								</Row>
								<Column gap="12">
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!createRoom
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											Create chat room
										</Text>
									</Row>
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!subscribe
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											Subscribe to room
										</Text>
									</Row>
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!rooms
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											List available rooms
										</Text>
									</Row>
								</Column>
							</Column>

							{/* Voice Management Commands Card */}
							<Column
								flex={1}
								gap="24"
								padding="24"
								background="surface"
								radius="l"
								border="neutral-alpha-weak"
								borderStyle="solid"
							>
								<Row gap="12" vertical="center">
									<Text variant="display-strong-xs">🎤</Text>
									<Heading as="h3" variant="heading-strong-m">
										Voice Tools
									</Heading>
								</Row>
								<Column gap="12">
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											/moveall
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											Move all users
										</Text>
									</Row>
									<Row gap="16" vertical="center">
										<Badge
											background="brand-alpha-weak"
											onBackground="brand-strong"
											textVariant="code-default-s"
											paddingX="8"
											paddingY="4"
										>
											!channels
										</Badge>
										<Text variant="body-default-s" onBackground="neutral-weak">
											List voice channels
										</Text>
									</Row>
								</Column>
							</Column>
						</Row>
					</Column>
				</RevealFx>
			</div>

			{/* Permissions Section */}
			<div id="permissions" style={{ width: "100%" }}>
				<RevealFx translateY="12" delay={0.8}>
					<Column fillWidth gap="24" paddingY="32">
						<Column horizontal="center" gap="16">
							<Heading as="h2" variant="heading-strong-l">
								🔒 Bot Permissions Explained
							</Heading>
							<Text
								variant="body-default-l"
								onBackground="neutral-weak"
								wrap="balance"
							>
								Balu requires Administrator permissions to provide full functionality across your Discord server
							</Text>
						</Column>
						
						<Row
							fillWidth
							gap="20"
							wrap
							s={{ direction: 'column' }}
							horizontal="center"
						>
							{/* Music Permissions */}
							<Column
								flex={1}
								gap="16"
								padding="20"
								background="surface"
								radius="l"
								border="neutral-alpha-weak"
								borderStyle="solid"
							>
								<Row gap="12" vertical="center">
									<Text variant="display-strong-s">🎵</Text>
									<Heading as="h3" variant="heading-strong-s">
										Music Features
									</Heading>
								</Row>
								<Column gap="8">
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Connect to Voice:</strong> Join any voice channel to play music
									</Text>
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Speak Permission:</strong> Stream high-quality audio
									</Text>
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Voice Activity:</strong> Detect playback status
									</Text>
								</Column>
							</Column>

							{/* Chat Management */}
							<Column
								flex={1}
								gap="16"
								padding="20"
								background="surface"
								radius="l"
								border="neutral-alpha-weak"
								borderStyle="solid"
							>
								<Row gap="12" vertical="center">
									<Text variant="display-strong-s">💬</Text>
									<Heading as="h3" variant="heading-strong-s">
										Chat Management
									</Heading>
								</Row>
								<Column gap="8">
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Send Messages:</strong> Respond to commands
									</Text>
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Embed Links:</strong> Rich music controls
									</Text>
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Manage Messages:</strong> Clean responses
									</Text>
								</Column>
							</Column>

							{/* Channel Management */}
							<Column
								flex={1}
								gap="16"
								padding="20"
								background="surface"
								radius="l"
								border="neutral-alpha-weak"
								borderStyle="solid"
							>
								<Row gap="12" vertical="center">
									<Text variant="display-strong-s">🔧</Text>
									<Heading as="h3" variant="heading-strong-s">
										Channel Tools
									</Heading>
								</Row>
								<Column gap="8">
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Manage Channels:</strong> Create and organize
									</Text>
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>Move Members:</strong> Voice management
									</Text>
									<Text variant="body-default-s" onBackground="neutral-weak">
										<strong>View All Channels:</strong> Full server access
									</Text>
								</Column>
							</Column>
						</Row>

						<Column horizontal="center" gap="12" paddingTop="16">
							<Badge
								background="accent-alpha-weak"
								onBackground="accent-strong"
								paddingX="12"
								paddingY="4"
							>
								✨ You can limit permissions in Discord server settings if needed
							</Badge>
						</Column>
					</Column>
				</RevealFx>
			</div>

			<div id="features">
				<Projects range={[1]} />
			</div>
			<div id="newsletter">
				<Mailchimp />
			</div>
		</Column>
	);
}
