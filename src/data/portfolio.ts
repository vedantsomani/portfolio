// Mock data for portfolio
export const personalInfo = {
  name: "Vedant Somani",
  role: "AI Developer & Researcher",
  tagline: "Building the future with artificial intelligence",
  bio: "Passionate AI developer and researcher specializing in machine learning, deep learning, and cutting-edge AI solutions. Currently working on innovative projects that push the boundaries of what's possible with artificial intelligence.",
  email: "vedant@example.com",
  phone: "+1 (555) 123-4567",
  location: "San Francisco, CA",
  github: "https://github.com/vedantsomani",
  linkedin: "https://linkedin.com/in/vedant-somani",
  twitter: "https://twitter.com/vedantsomani",
  resume: "/resume.pdf"
}

export const skills = [
  {
    category: "AI & Machine Learning",
    items: [
      { name: "TensorFlow", level: 95 },
      { name: "PyTorch", level: 92 },
      { name: "Scikit-learn", level: 88 },
      { name: "Keras", level: 85 },
      { name: "OpenAI API", level: 90 },
      { name: "Hugging Face", level: 87 }
    ]
  },
  {
    category: "Programming Languages",
    items: [
      { name: "Python", level: 95 },
      { name: "JavaScript", level: 88 },
      { name: "TypeScript", level: 85 },
      { name: "R", level: 75 },
      { name: "SQL", level: 80 },
      { name: "Java", level: 70 }
    ]
  },
  {
    category: "Web Development",
    items: [
      { name: "React", level: 90 },
      { name: "Next.js", level: 85 },
      { name: "Node.js", level: 82 },
      { name: "FastAPI", level: 88 },
      { name: "Django", level: 80 },
      { name: "MongoDB", level: 75 }
    ]
  },
  {
    category: "Tools & Platforms",
    items: [
      { name: "Docker", level: 85 },
      { name: "AWS", level: 80 },
      { name: "Git", level: 92 },
      { name: "Jupyter", level: 95 },
      { name: "Linux", level: 85 },
      { name: "CI/CD", level: 78 }
    ]
  }
]

export const projects = [
  {
    id: 1,
    title: "AI-Powered Content Generator",
    description: "A sophisticated content generation platform using GPT-4 and custom fine-tuned models. Features include multi-modal content creation, sentiment analysis, and automated content optimization.",
    image: "/projects/ai-content-generator.jpg",
    technologies: ["Python", "OpenAI API", "FastAPI", "React", "PostgreSQL"],
    github: "https://github.com/vedantsomani/ai-content-generator",
    demo: "https://ai-content-gen.vercel.app",
    featured: true,
    category: "AI/ML"
  },
  {
    id: 2,
    title: "Neural Network Visualizer",
    description: "Interactive web application for visualizing neural network architectures and training processes. Built with Three.js for 3D visualization and real-time training metrics.",
    image: "/projects/nn-visualizer.jpg",
    technologies: ["React", "Three.js", "TensorFlow.js", "D3.js", "WebGL"],
    github: "https://github.com/vedantsomani/neural-network-visualizer",
    demo: "https://nn-visualizer.vercel.app",
    featured: true,
    category: "Web Dev"
  },
  {
    id: 3,
    title: "Predictive Analytics Dashboard",
    description: "Comprehensive analytics platform for business intelligence with machine learning-powered predictions. Includes real-time data processing and interactive visualizations.",
    image: "/projects/analytics-dashboard.jpg",
    technologies: ["Python", "Scikit-learn", "Streamlit", "Plotly", "Apache Kafka"],
    github: "https://github.com/vedantsomani/predictive-analytics",
    demo: "https://analytics-dashboard.streamlit.app",
    featured: false,
    category: "AI/ML"
  },
  {
    id: 4,
    title: "Smart Home IoT System",
    description: "End-to-end IoT solution for smart home automation with AI-powered energy optimization. Features voice control, predictive maintenance, and automated scheduling.",
    image: "/projects/smart-home.jpg",
    technologies: ["Python", "Raspberry Pi", "MQTT", "TensorFlow", "React Native"],
    github: "https://github.com/vedantsomani/smart-home-iot",
    demo: "https://smart-home-demo.vercel.app",
    featured: false,
    category: "IoT"
  },
  {
    id: 5,
    title: "Computer Vision API",
    description: "RESTful API for computer vision tasks including object detection, facial recognition, and image classification. Built with FastAPI and deployed on AWS.",
    image: "/projects/cv-api.jpg",
    technologies: ["Python", "OpenCV", "FastAPI", "AWS Lambda", "Docker"],
    github: "https://github.com/vedantsomani/computer-vision-api",
    demo: "https://cv-api.herokuapp.com/docs",
    featured: false,
    category: "AI/ML"
  },
  {
    id: 6,
    title: "Blockchain Voting System",
    description: "Secure, transparent voting system built on Ethereum blockchain with React frontend. Features voter authentication, real-time results, and audit trails.",
    image: "/projects/blockchain-voting.jpg",
    technologies: ["Solidity", "Web3.js", "React", "Truffle", "MetaMask"],
    github: "https://github.com/vedantsomani/blockchain-voting",
    demo: "https://blockchain-voting.vercel.app",
    featured: false,
    category: "Blockchain"
  }
]

export const experience = [
  {
    company: "TechCorp AI",
    position: "Senior AI Developer",
    duration: "2022 - Present",
    description: "Leading AI research and development projects, specializing in natural language processing and computer vision solutions.",
    technologies: ["Python", "TensorFlow", "AWS", "Docker"]
  },
  {
    company: "InnovateLab",
    position: "Machine Learning Engineer",
    duration: "2020 - 2022",
    description: "Developed and deployed ML models for various client projects, focusing on predictive analytics and recommendation systems.",
    technologies: ["Python", "Scikit-learn", "MLflow", "Kubernetes"]
  },
  {
    company: "StartupX",
    position: "Full Stack Developer",
    duration: "2019 - 2020",
    description: "Built responsive web applications and APIs, collaborated with cross-functional teams to deliver high-quality software solutions.",
    technologies: ["React", "Node.js", "MongoDB", "Express"]
  }
]

export const education = [
  {
    degree: "Master of Science in Computer Science",
    school: "Stanford University",
    duration: "2017 - 2019",
    description: "Specialization in Artificial Intelligence and Machine Learning"
  },
  {
    degree: "Bachelor of Science in Computer Engineering",
    school: "UC Berkeley",
    duration: "2013 - 2017",
    description: "Magna Cum Laude, Dean's List"
  }
]

export const testimonials = [
  {
    name: "Sarah Johnson",
    position: "CTO at TechCorp",
    content: "Vedant's expertise in AI and machine learning is exceptional. His innovative solutions have transformed our business processes.",
    avatar: "/testimonials/sarah.jpg"
  },
  {
    name: "Michael Chen",
    position: "Product Manager at InnovateLab",
    content: "Working with Vedant was a game-changer. His ability to translate complex AI concepts into practical solutions is remarkable.",
    avatar: "/testimonials/michael.jpg"
  },
  {
    name: "Emily Rodriguez",
    position: "Data Scientist at DataFlow",
    content: "Vedant's deep understanding of both frontend and backend technologies makes him an invaluable team member.",
    avatar: "/testimonials/emily.jpg"
  }
]
