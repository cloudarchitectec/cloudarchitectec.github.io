# Cloud Architect EC

[![Deploy Hugo site to Pages](https://github.com/cloudarchitectec/cloudarchitectec.github.io/actions/workflows/hugo.yml/badge.svg)](https://github.com/cloudarchitectec/cloudarchitectec.github.io/actions/workflows/hugo.yml)

> 澳洲雲端架構師 EC 的技術部落格 | Cloud Architect EC's Tech Blog

🌐 **Live Site**: [https://cloudarchitectec.github.io](https://cloudarchitectec.github.io)

## About

This repository hosts the source code for Cloud Architect EC's technical blog, built with [Hugo](https://gohugo.io/) and the [PaperMod](https://github.com/adityatelange/hugo-PaperMod) theme.

### Topics Covered
- ☁️ Cloud Architecture (AWS, Azure)
- 🛠️ DevOps & Infrastructure
- 📚 Tech Career & Professional Development
- 🇦🇺 Tech Life in Australia
- 📝 Technical Tutorials & Guides

## Tech Stack

- **Static Site Generator**: [Hugo](https://gohugo.io/) (v0.135.0+)
- **Theme**: [PaperMod](https://github.com/adityatelange/hugo-PaperMod)
- **Deployment**: GitHub Actions → GitHub Pages
- **Languages**: Traditional Chinese (Primary), English
- **Dependencies**: TailwindCSS (via npm)

## Features

- 🌙 Dark/Light mode toggle
- 📱 Fully responsive design
- 🔍 Built-in search functionality
- 📊 Reading time estimation
- 🔗 Social sharing buttons
- 🧭 Breadcrumb navigation
- 📋 Code copy buttons
- 🏷️ Tag and category system
- 🌐 Multilingual support

## Quick Start

### Prerequisites
- Hugo Extended v0.135.0+
- Git
- Node.js (for dependencies)

### Local Development
```bash
# Clone the repository
git clone https://github.com/cloudarchitectec/cloudarchitectec.github.io.git
cd cloudarchitectec.github.io

# Initialize theme submodule
git submodule update --init --recursive

# Install dependencies
npm install

# Start development server
hugo server --bind 0.0.0.0 --port 1313
```

Visit `http://localhost:1313` to view the site locally.

## Deployment

The site automatically deploys to GitHub Pages when changes are pushed to the `main` branch.

- **Deployment**: Automatic via GitHub Actions
- **Trigger**: Push to `main` branch
- **Build Time**: ~2-3 minutes
- **Live URL**: https://cloudarchitectec.github.io

## Project Structure

```
├── content/posts/          # Blog post content
├── static/                 # Static assets (images, favicons)
├── themes/PaperMod/        # Hugo theme (submodule)
├── .github/workflows/      # GitHub Actions
├── hugo.toml              # Hugo configuration
└── package.json           # Node.js dependencies
```

## Contributing

This is a personal blog repository. While contributions are not expected, feel free to:
- 🐛 Report issues
- 💡 Suggest improvements
- 🔗 Share interesting resources

## License

Content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Code is licensed under [MIT License](https://opensource.org/licenses/MIT).

## Connect

- 🌐 Blog: [cloudarchitectec.github.io](https://cloudarchitectec.github.io)
- 💼 GitHub: [@cloudarchitectec](https://github.com/cloudarchitectec)

---

*Built with ❤️ using Hugo and PaperMod*