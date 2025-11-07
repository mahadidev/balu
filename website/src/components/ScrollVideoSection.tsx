'use client';

import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// Register GSAP plugin
gsap.registerPlugin(ScrollTrigger);

const ScrollVideoSection = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    const section = sectionRef.current;

    if (!video || !section) return;

    // Ensure video is loaded
    video.addEventListener('loadedmetadata', () => {
      const videoDuration = video.duration;

      // Create ScrollTrigger for the pinned video section
      ScrollTrigger.create({
        trigger: section,
        start: 'top top',
        end: '+=200%', // Pin for 200% of viewport height to allow scrubbing
        pin: true,
        scrub: 1, // Smooth scrubbing
        onUpdate: (self) => {
          // Update video currentTime based on scroll progress
          const progress = self.progress;
          video.currentTime = progress * videoDuration;
        },
        onLeave: () => {
          // Ensure video is at the end when leaving
          video.currentTime = videoDuration;
        },
        onEnterBack: () => {
          // Reset video when scrolling back up
          video.currentTime = 0;
        }
      });
    });

    // Cleanup
    return () => {
      ScrollTrigger.getAll().forEach(trigger => {
        if (trigger.trigger === section) {
          trigger.kill();
        }
      });
    };
  }, []);

  return (
    <div 
      ref={sectionRef}
      className="scroll-video-section relative w-full h-screen overflow-hidden bg-black"
    >
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover"
        src="/images/slides/chat_room_slide_1.mp4"
        muted
        playsInline
        preload="auto"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover'
        }}
      />
      
      {/* Optional overlay content */}
      <div className="absolute inset-0 flex items-center justify-center z-10">
        <div className="text-center text-white">
          <h2 className="text-4xl md:text-6xl font-bold mb-4">
            Cross Server Chat Room
          </h2>
          <p className="text-xl md:text-2xl opacity-90">
            Connect Discord servers with room-based communication
          </p>
        </div>
      </div>
      
      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
        <div className="text-white text-center">
          <div className="animate-bounce">
            <svg 
              className="w-6 h-6 mx-auto mb-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M19 14l-7 7m0 0l-7-7m7 7V3" 
              />
            </svg>
          </div>
          <p className="text-sm opacity-75">Scroll to explore</p>
        </div>
      </div>
    </div>
  );
};

export default ScrollVideoSection;