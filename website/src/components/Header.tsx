"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Fade, Flex, Line, Row, ToggleButton } from "@once-ui-system/core";

import { display, person } from "@/resources";
import styles from "./Header.module.scss";
import { ThemeToggle } from "./ThemeToggle";

type TimeDisplayProps = {
  timeZone: string;
  locale?: string; // Optionally allow locale, defaulting to 'en-GB'
};

const TimeDisplay: React.FC<TimeDisplayProps> = ({ timeZone, locale = "en-GB" }) => {
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        timeZone,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      };
      const timeString = new Intl.DateTimeFormat(locale, options).format(now);
      setCurrentTime(timeString);
    };

    updateTime();
    const intervalId = setInterval(updateTime, 1000);

    return () => clearInterval(intervalId);
  }, [timeZone, locale]);

  return <>{currentTime}</>;
};

export default TimeDisplay;

export const Header = () => {
  const pathname = usePathname();
  const [activeSection, setActiveSection] = useState("home");
  const isHomePage = pathname === "/";

  const scrollToSection = (sectionId: string) => {
    if (!isHomePage) {
      // Navigate to home page with hash
      window.location.href = `/#${sectionId}`;
      return;
    }
    
    const element = document.getElementById(sectionId);
    if (element) {
      const elementPosition = element.offsetTop;
      const offsetPosition = elementPosition - 0; // 120px offset from top
      
      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth"
      });
      setActiveSection(sectionId);
    }
  };

  useEffect(() => {
    // Reset active section when not on home page
    if (!isHomePage) {
      setActiveSection("");
      return;
    }

    const handleScroll = () => {
      const sections = ["home", "commands", "permissions", "features", "newsletter"];
      const scrollPosition = window.scrollY + 200; // Offset for header

      for (let i = sections.length - 1; i >= 0; i--) {
        const section = document.getElementById(sections[i]);
        if (section) {
          // Check if at bottom of page
          if(window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 10){
            setActiveSection(sections[sections.length - 1]);
            return; // Exit the function early to prevent override
          }
          if (section.offsetTop <= scrollPosition) {
            setActiveSection(sections[i]);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Call once to set initial state
    return () => window.removeEventListener('scroll', handleScroll);
  }, [isHomePage]);

  return (
		<>
			<Fade
				s={{ hide: true }}
				fillWidth
				position="fixed"
				height="80"
				zIndex={9}
			/>
			<Fade
				hide
				s={{ hide: false }}
				fillWidth
				position="fixed"
				bottom="0"
				to="top"
				height="80"
				zIndex={9}
			/>
			<Row
				fitHeight
				className={styles.position}
				position="sticky"
				as="header"
				zIndex={9}
				fillWidth
				padding="8"
				horizontal="center"
				data-border="rounded"
				s={{
					position: 'fixed',
				}}
			>
				<Row
					paddingLeft="12"
					fillWidth
					vertical="center"
					textVariant="body-default-s"
				>
					{display.location && <Row s={{ hide: true }}>{person.location}</Row>}
				</Row>
				<Row fillWidth horizontal="center">
					<Row
						background="page"
						border="neutral-alpha-weak"
						radius="m-4"
						shadow="l"
						padding="4"
						s={{ padding: "2" }}
						horizontal="center"
						zIndex={1}
					>
						<Row
							gap="4"
							s={{ gap: "2" }}
							vertical="center"
							textVariant="body-default-s"
							suppressHydrationWarning
						>
							<ToggleButton
								prefixIcon="home"
								onClick={() => scrollToSection('home')}
								selected={activeSection === 'home'}
							/>
							<Line background="neutral-alpha-medium" vert maxHeight="24" />
							<Row s={{ hide: true }}>
								<ToggleButton
									prefixIcon="search"
									onClick={() => scrollToSection('commands')}
									label="Commands"
									selected={activeSection === 'commands'}
								/>
							</Row>
							<Row hide s={{ hide: false }}>
								<ToggleButton
									prefixIcon="search"
									onClick={() => scrollToSection('commands')}
									selected={activeSection === 'commands'}
								/>
							</Row>
							<Row s={{ hide: true }}>
								<ToggleButton
									prefixIcon="check"
									onClick={() => scrollToSection('permissions')}
									label="Permissions"
									selected={activeSection === 'permissions'}
								/>
							</Row>
							<Row hide s={{ hide: false }}>
								<ToggleButton
									prefixIcon="check"
									onClick={() => scrollToSection('permissions')}
									selected={activeSection === 'permissions'}
								/>
							</Row>
							<Row s={{ hide: true }}>
								<ToggleButton
									prefixIcon="grid"
									onClick={() => scrollToSection('features')}
									label="Features"
									selected={activeSection === 'features'}
								/>
							</Row>
							<Row hide s={{ hide: false }}>
								<ToggleButton
									prefixIcon="grid"
									onClick={() => scrollToSection('features')}
									selected={activeSection === 'features'}
								/>
							</Row>
							<Row s={{ hide: true }}>
								<ToggleButton
									prefixIcon="globe"
									onClick={() => scrollToSection('newsletter')}
									label="Newsletter"
									selected={activeSection === 'newsletter'}
								/>
							</Row>
							<Row hide s={{ hide: false }}>
								<ToggleButton
									prefixIcon="globe"
									onClick={() => scrollToSection('newsletter')}
									selected={activeSection === 'newsletter'}
								/>
							</Row>
							{display.themeSwitcher && (
								<>
									<Line background="neutral-alpha-medium" vert maxHeight="24" />
									<ThemeToggle />
								</>
							)}
						</Row>
					</Row>
				</Row>
				<Flex fillWidth horizontal="end" vertical="center">
					<Flex
						paddingRight="12"
						horizontal="end"
						vertical="center"
						textVariant="body-default-s"
						gap="20"
					>
						<Flex s={{ hide: true }}>
							{display.time && <TimeDisplay timeZone={person.location} />}
						</Flex>
					</Flex>
				</Flex>
			</Row>
		</>
	);
};
