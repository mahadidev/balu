import { About, Blog, Gallery, Home, Newsletter, Person, Social, Work } from "@/types";
import { Line, Logo, Row, Text } from "@once-ui-system/core";

const person: Person = {
  firstName: "Balu",
  lastName: "",
  name: `Balu`,
  role: "Discord Bot",
  avatar: "/images/logo.png",
  email: "mahadi.dev.pm@gmail.com",
  location: "UTC", // Expecting the IANA time zone identifier, e.g., 'Europe/Vienna'
  languages: ["English"], // optional: Leave the array empty if you don't want to display languages
};

const newsletter: Newsletter = {
  display: true,
  title: <>Get {person.firstName} Bot Updates</>,
  description: <>Stay updated with new features and improvements for Discord servers</>,
};

const social: Social = [
  // Links are automatically displayed.
  // Import new icons in /once-ui/icons.ts
  {
    name: "Discord",
    icon: "discord",
    link: "https://discord.gg/wy7Gzv68",
  },
  {
    name: "Facebook",
    icon: "facebook",
    link: "https://www.facebook.com/baluBot322",
  },
  {
    name: "Support",
    icon: "email",
    link: `mailto:${person.email}`,
  },
];

const home: Home = {
	path: '/',
	image: '/images/og/opengraph-image.png',
	label: 'Home',
	title: `${person.name} - Discord Bot`,
	description: `Advanced Discord bot with music, chat, and voice management features`,
	headline: <>Your all-in-one Discord server companion</>,
	featured: {
		display: true,
		title: (
			<Row gap="12" vertical="center">
				<Text marginRight="4" onBackground="brand-medium">
					Cross Server Chat
				</Text>{' '}
				<Line background="brand-alpha-strong" vert height="20" />
				<Text marginRight="4" onBackground="brand-medium">
					Music Player
				</Text>{' '}
				<Line background="brand-alpha-strong" vert height="20" />
				<Text marginRight="4" onBackground="brand-medium">
					Voice Tools
				</Text>
			</Row>
		),
		href: '/work/music-player-system',
	},
	subline: (
		<>
			Meet Balu, your powerful Discord companion that brings advanced
			<br /> music streaming, cross server chat rooms, and voice management to
			your server.
		</>
	),
};

const about: About = {
	path: 'https://discord.com/oauth2/authorize?client_id=1427000830384672950',
	label: 'Features',
	title: `Install Now`,
	description: `Discover all the powerful features that ${person.name} brings to your Discord server`,
	tableOfContent: {
		display: true,
		subItems: false,
	},
	avatar: {
		display: false,
	},
	calendar: {
		display: false,
		link: 'https://discord.gg/balu-bot',
	},
	intro: {
		display: true,
		title: 'Overview',
		description: (
			<>
				Balu is a comprehensive Discord bot designed to enhance your server
				experience with advanced music streaming, cross-server communication,
				and intelligent voice management. Built with reliability and ease of use
				in mind.
			</>
		),
	},
	work: {
		display: true, // set to false to hide this section
		title: 'Core Features',
		experiences: [
			{
				company: '🎵 Music Player',
				timeframe: 'v2.0+',
				role: 'Advanced Audio Streaming',
				achievements: [
					<>
						High-quality YouTube music streaming with queue management, playlist
						support, and seamless playback controls including repeat and shuffle
						modes.
					</>,
					<>
						Interactive music interface with play/pause, skip, volume control,
						and real-time progress tracking for the ultimate listening
						experience.
					</>,
					<>
						Smart Related Songs feature with intelligent genre detection - use
						--related to automatically find and queue similar music based on
						language, genre, and era.
					</>,
				],
				images: [],
			},
			{
				company: '🌐 Cross Server Chat Room',
				timeframe: 'v2.0+',
				role: 'Room-Based Cross-Server Communication',
				achievements: [
					<>
						Create and join topic-specific chat rooms that connect multiple
						Discord servers with intelligent rate limiting, content filtering,
						and room-based organization.
					</>,
					<>
						Real-time message broadcasting within rooms with attachment support,
						simple subscription commands (!subscribe, !createRoom), and both
						text/slash commands.
					</>,
				],
				images: [],
			},
		],
	},
	studies: {
		display: true, // set to false to hide this section
		title: 'Additional Features',
		institutions: [
			{
				name: '🎤 Voice Management',
				description: (
					<>
						Move users between voice channels effortlessly with advanced
						permissions and bulk operations.
					</>
				),
			},
			{
				name: '🏠 Room Management',
				description: (
					<>
						Create and manage topic-specific chat rooms with easy subscription
						commands and cross-server communication.
					</>
				),
			},
		],
	},
	technical: {
		display: true, // set to false to hide this section
		title: 'Technical Stack',
		skills: [
			{
				title: 'Discord.py',
				description: (
					<>
						Built with modern Python and Discord.py for reliable,
						high-performance bot operations.
					</>
				),
				tags: [
					{
						name: 'Python',
						icon: 'python',
					},
					{
						name: 'Discord',
						icon: 'discord',
					},
				],
				images: [],
			},
			{
				title: 'Advanced Features',
				description: (
					<>
						Includes database management, async operations, error handling, and
						auto-reconnection.
					</>
				),
				tags: [
					{
						name: 'SQLite',
						icon: 'database',
					},
					{
						name: 'Async',
						icon: 'code',
					},
				],
				images: [],
			},
		],
	},
};

const blog: Blog = {
  path: "/blog",
  label: "Updates",
  title: "Bot updates and changelogs...",
  description: `Latest updates and improvements for ${person.name}`,
  // Create new blog posts by adding a new .mdx file to app/blog/posts
  // All posts will be listed on the /blog route
};

const work: Work = {
  path: "/work",
  label: "Commands",
  title: `Commands – ${person.name}`,
  description: `Complete command reference for ${person.name}`,
  // Create new project pages by adding a new .mdx file to app/blog/posts
  // All projects will be listed on the /home and /work routes
};

const gallery: Gallery = {
  path: "/gallery",
  label: "Screenshots",
  title: `Screenshots – ${person.name}`,
  description: `See ${person.name} in action across different Discord servers`,
  // Images by https://lorant.one
  // These are placeholder images, replace with your own
  images: [
    {
      src: "/images/gallery/horizontal-1.jpg",
      alt: "image",
      orientation: "horizontal",
    },
    {
      src: "/images/gallery/vertical-4.jpg",
      alt: "image",
      orientation: "vertical",
    },
    {
      src: "/images/gallery/horizontal-3.jpg",
      alt: "image",
      orientation: "horizontal",
    },
    {
      src: "/images/gallery/vertical-1.jpg",
      alt: "image",
      orientation: "vertical",
    },
    {
      src: "/images/gallery/vertical-2.jpg",
      alt: "image",
      orientation: "vertical",
    },
    {
      src: "/images/gallery/horizontal-2.jpg",
      alt: "image",
      orientation: "horizontal",
    },
    {
      src: "/images/gallery/horizontal-4.jpg",
      alt: "image",
      orientation: "horizontal",
    },
    {
      src: "/images/gallery/vertical-3.jpg",
      alt: "image",
      orientation: "vertical",
    },
  ],
};

export { about, blog, gallery, home, newsletter, person, social, work };

