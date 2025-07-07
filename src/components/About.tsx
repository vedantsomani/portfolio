'use client'

import { motion } from 'framer-motion'
import { User, MapPin, Calendar, Award } from 'lucide-react'
import { personalInfo, experience, education } from '@/data/portfolio'

export default function About() {
  return (
    <section id="about" className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">About Me</h2>
          <p className="text-xl text-white/60 max-w-2xl mx-auto">
            Get to know more about my journey, experience, and passion for technology
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
          {/* Personal Info */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="glass-card p-8"
          >
            <div className="flex items-center mb-6">
              <User className="w-6 h-6 text-blue-400 mr-3" />
              <h3 className="text-2xl font-bold text-white">Personal Info</h3>
            </div>
            
            <p className="text-white/80 mb-6 leading-relaxed">
              {personalInfo.bio}
            </p>
            
            <div className="space-y-3">
              <div className="flex items-center text-white/60">
                <MapPin className="w-4 h-4 mr-2" />
                <span>{personalInfo.location}</span>
              </div>
              <div className="flex items-center text-white/60">
                <Calendar className="w-4 h-4 mr-2" />
                <span>Available for new opportunities</span>
              </div>
            </div>
          </motion.div>

          {/* Quick Stats */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="glass-card p-8"
          >
            <div className="flex items-center mb-6">
              <Award className="w-6 h-6 text-purple-400 mr-3" />
              <h3 className="text-2xl font-bold text-white">Quick Stats</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">5+</div>
                <div className="text-white/60">Years Experience</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-400 mb-2">50+</div>
                <div className="text-white/60">Projects Completed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-pink-400 mb-2">10+</div>
                <div className="text-white/60">Technologies</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">3</div>
                <div className="text-white/60">Awards Won</div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Experience */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h3 className="text-3xl font-bold text-white mb-8 text-center">Experience</h3>
          <div className="space-y-6">
            {experience.map((exp, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                viewport={{ once: true }}
                className="glass-card p-6"
              >
                <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
                  <div>
                    <h4 className="text-xl font-bold text-white">{exp.position}</h4>
                    <p className="text-blue-400 font-semibold">{exp.company}</p>
                  </div>
                  <span className="text-white/60 mt-2 md:mt-0">{exp.duration}</span>
                </div>
                <p className="text-white/80 mb-4">{exp.description}</p>
                <div className="flex flex-wrap gap-2">
                  {exp.technologies.map((tech, techIndex) => (
                    <span
                      key={techIndex}
                      className="px-3 py-1 bg-white/10 text-white/80 rounded-full text-sm"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Education */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h3 className="text-3xl font-bold text-white mb-8 text-center">Education</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {education.map((edu, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                viewport={{ once: true }}
                className="glass-card p-6"
              >
                <h4 className="text-xl font-bold text-white mb-2">{edu.degree}</h4>
                <p className="text-blue-400 font-semibold mb-2">{edu.school}</p>
                <p className="text-white/60 mb-3">{edu.duration}</p>
                <p className="text-white/80">{edu.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
