'use client';

import { Button } from '@once-ui-system/core';

const HeroSection = () => {
  return (
    <section className="hero-section relative w-full h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      {/* Background pattern or animation */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.1),transparent)]"></div>
      </div>
      
      {/* Hero content */}
      <div className="relative z-10 text-center text-white max-w-4xl mx-auto px-6">
        <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
          Meet <span className="text-blue-400">Balu</span>
        </h1>
        
        <p className="text-xl md:text-2xl mb-8 opacity-90 max-w-2xl mx-auto">
          Your all-in-one Discord server companion bringing advanced music streaming, 
          cross server chat rooms, and voice management to your server.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button
            href="https://discord.com/oauth2/authorize?client_id=1427000830384672950"
            size="l"
            variant="primary"
            className="px-8 py-4 text-lg font-semibold"
          >
            Add to Discord
          </Button>
          
          <Button
            href="#features"
            size="l" 
            variant="secondary"
            className="px-8 py-4 text-lg font-semibold"
          >
            Learn More
          </Button>
        </div>
        
        {/* Feature highlights */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div className="p-4">
            <div className="text-3xl mb-2">🎵</div>
            <h3 className="text-lg font-semibold mb-1">Music Player</h3>
            <p className="text-sm opacity-75">High-quality YouTube streaming</p>
          </div>
          
          <div className="p-4">
            <div className="text-3xl mb-2">🌐</div>
            <h3 className="text-lg font-semibold mb-1">Cross Server Chat</h3>
            <p className="text-sm opacity-75">Connect multiple Discord servers</p>
          </div>
          
          <div className="p-4">
            <div className="text-3xl mb-2">🎤</div>
            <h3 className="text-lg font-semibold mb-1">Voice Tools</h3>
            <p className="text-sm opacity-75">Advanced voice management</p>
          </div>
        </div>
      </div>
      
      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
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
          <p className="text-sm opacity-75">Scroll down</p>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;