import Hero from '@/components/Hero'
import About from '@/components/About'
import Projects from '@/components/Projects'
import Skills from '@/components/Skills'
import Contact from '@/components/Contact'

export default function Home() {
  return (
    <div className="relative">
      <Hero />
      <About />
      <Projects />
      <Skills />
      <Contact />
    </div>
  )
}
