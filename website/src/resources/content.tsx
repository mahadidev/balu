import { About, Blog, Gallery, Home, Newsletter, Person, Social, Work } from "@/types";
import { Line, Logo, Row, Text } from "@once-ui-system/core";

const person: Person = {
  firstName: "Balu",
  lastName: "",
  name: `Balu`,
  role: "Discord Bot",
  avatar: "/images/avatar.jpg",
  email: "balu@discord.com",
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
    name: "GitHub",
    icon: "github",
    link: "https://github.com/mahadihasan/balu-bot",
  },
  {
    name: "Discord",
    icon: "discord",
    link: "https://discord.gg/balu-bot",
  },
  {
    name: "Support",
    icon: "email",
    link: `mailto:${person.email}`,
  },
];

const home: Home = {
  path: "/",
  image: "/images/og/home.jpg",
  label: "Home",
  title: `${person.name} - Discord Bot`,
  description: `Advanced Discord bot with music, chat, and voice management features`,
  headline: <>Your all-in-one Discord server companion</>,
  featured: {
    display: true,
    title: (
      <Row gap="12" vertical="center">
        <strong className="ml-4">🎵 Music Player</strong>{" "}
        <Line background="brand-alpha-strong" vert height="20" />
        <Text marginRight="4" onBackground="brand-medium">
          Featured feature
        </Text>
      </Row>
    ),
    href: "/work/music-player-system",
  },
  subline: (
    <>
      Meet Balu, your powerful Discord companion that brings advanced
      <br /> music streaming, global chat, and voice management to your server.
    </>
  ),
};

const about: About = {
  path: "/about",
  label: "Features",
  title: `Features – ${person.name}`,
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
    link: "https://discord.gg/balu-bot",
  },
  intro: {
    display: true,
    title: "Overview",
    description: (
      <>
        Balu is a comprehensive Discord bot designed to enhance your server experience with 
        advanced music streaming, cross-server communication, and intelligent voice management. 
        Built with reliability and ease of use in mind.
      </>
    ),
  },
  work: {
    display: true, // set to false to hide this section
    title: "Core Features",
    experiences: [
      {
        company: "🎵 Music Player",
        timeframe: "v2.0+",
        role: "Advanced Audio Streaming",
        achievements: [
          <>
            High-quality YouTube music streaming with queue management, playlist support,
            and seamless playback controls including repeat and shuffle modes.
          </>,
          <>
            Interactive music interface with play/pause, skip, volume control, and
            real-time progress tracking for the ultimate listening experience.
          </>,
        ],
        images: [],
      },
      {
        company: "🌐 Global Chat",
        timeframe: "v1.5+",
        role: "Cross-Server Communication",
        achievements: [
          <>
            Connect multiple Discord servers through secure global chat channels with
            intelligent rate limiting and content filtering for safe communication.
          </>,
          <>
            Real-time message broadcasting across servers with attachment support,
            moderation tools, and comprehensive logging for server administrators.
          </>,
        ],
        images: [],
      },
    ],
  },
  studies: {
    display: true, // set to false to hide this section
    title: "Additional Features",
    institutions: [
      {
        name: "🎤 Voice Management",
        description: <>Move users between voice channels effortlessly with advanced permissions and bulk operations.</>,
      },
      {
        name: "📂 Category Chat",
        description: <>Organize conversations with category-based chat systems and intelligent channel management.</>,
      },
    ],
  },
  technical: {
    display: true, // set to false to hide this section
    title: "Technical Stack",
    skills: [
      {
        title: "Discord.py",
        description: (
          <>Built with modern Python and Discord.py for reliable, high-performance bot operations.</>
        ),
        tags: [
          {
            name: "Python",
            icon: "python",
          },
          {
            name: "Discord",
            icon: "discord",
          },
        ],
        images: [],
      },
      {
        title: "Advanced Features",
        description: (
          <>Includes database management, async operations, error handling, and auto-reconnection.</>
        ),
        tags: [
          {
            name: "SQLite",
            icon: "database",
          },
          {
            name: "Async",
            icon: "code",
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

export { person, social, newsletter, home, about, blog, work, gallery };
