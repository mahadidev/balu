import { Globe, Gamepad2, Users, Shield, ChevronRight } from 'lucide-react'
import Image from 'next/image'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 to-black text-white overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-black/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3 group">
              <Image 
                src="/logo.png" 
                alt="Balu Bot Logo" 
                width={28} 
                height={28} 
                className="rounded transition-transform group-hover:scale-110" 
              />
              <span className="text-lg font-medium bg-gradient-to-r from-red-400 to-red-600 bg-clip-text text-transparent">
                Balu
              </span>
            </div>
            <button className="bg-red-600 hover:bg-red-500 px-6 py-2 rounded-full transition-all duration-300 hover:shadow-lg hover:shadow-red-600/25 flex items-center space-x-2 group">
              <span className="text-sm font-medium">Add to Discord</span>
              <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-12 animate-fade-in">
            <Image 
              src="/banner.png" 
              alt="Balu Bot Banner" 
              width={320} 
              height={160} 
              className="mx-auto rounded-2xl shadow-2xl hover:scale-105 transition-transform duration-700" 
            />
          </div>
          
          <h1 className="text-6xl md:text-8xl font-bold mb-8 tracking-tight animate-slide-up">
            <span className="bg-gradient-to-r from-red-500 to-red-400 bg-clip-text text-transparent">
              Balu
            </span>
          </h1>
          
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed animate-slide-up-delay">
            A powerful Discord bot for global chat, music, and community management
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up-delay-2">
            <button className="bg-red-600 hover:bg-red-500 px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:shadow-xl hover:shadow-red-600/25 hover:-translate-y-1 flex items-center justify-center space-x-2 group">
              <span>Get Started</span>
              <ChevronRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </button>
            <button className="border border-white/20 hover:border-white/40 px-8 py-4 rounded-full text-lg font-medium transition-all duration-300 hover:bg-white/5">
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Core Features
            </h2>
            <p className="text-gray-400 text-lg">Everything you need for your Discord community</p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { icon: Globe, title: "Global Chat", desc: "Cross-server messaging" },
              { icon: Gamepad2, title: "Music Player", desc: "High-quality streaming" },
              { icon: Users, title: "Voice Tools", desc: "Dynamic channel management" },
              { icon: Shield, title: "Moderation", desc: "Advanced security tools" }
            ].map((feature, index) => (
              <div 
                key={feature.title}
                className="group p-6 rounded-2xl bg-gradient-to-b from-white/5 to-white/0 border border-white/10 hover:border-red-500/30 transition-all duration-500 hover:-translate-y-2 hover:shadow-xl hover:shadow-red-500/10"
                style={{ animationDelay: `${index * 150}ms` }}
              >
                <feature.icon className="h-8 w-8 text-red-500 mb-4 group-hover:scale-110 transition-transform duration-300" />
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Start */}
      <section className="py-24 px-6 bg-gradient-to-r from-red-950/20 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-12 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            Get Started in Seconds
          </h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "1", title: "Invite", desc: "Add Balu to your Discord server" },
              { step: "2", title: "Configure", desc: "Set up permissions and features" },
              { step: "3", title: "Enjoy", desc: "Start using all powerful features" }
            ].map((item, index) => (
              <div 
                key={item.step}
                className="group"
                style={{ animationDelay: `${index * 200}ms` }}
              >
                <div className="w-12 h-12 bg-red-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-lg font-bold group-hover:scale-110 transition-transform duration-300">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-gray-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-12 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <Image src="/logo.png" alt="Balu Bot Logo" width={20} height={20} className="rounded" />
            <span className="font-medium bg-gradient-to-r from-red-400 to-red-600 bg-clip-text text-transparent">
              Balu Bot
            </span>
          </div>
          <p className="text-gray-400 mb-6">
            Built for Discord communities with ❤️
          </p>
          <div className="flex justify-center space-x-8 text-sm text-gray-500">
            <a href="#" className="hover:text-red-400 transition-colors">Privacy</a>
            <a href="#" className="hover:text-red-400 transition-colors">Terms</a>
            <a href="#" className="hover:text-red-400 transition-colors">Support</a>
          </div>
        </div>
      </footer>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fade-in {
          animation: fadeIn 1s ease-out;
        }
        
        .animate-slide-up {
          animation: slideUp 0.8s ease-out;
        }
        
        .animate-slide-up-delay {
          animation: slideUp 0.8s ease-out 0.2s both;
        }
        
        .animate-slide-up-delay-2 {
          animation: slideUp 0.8s ease-out 0.4s both;
        }
      `}</style>
    </div>
  )
}
