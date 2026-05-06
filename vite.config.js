import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
  build: {
    // Output landet in static/dist/ — collectstatic propagiert das danach
    // mit Hash + Manifest-Eintrag in staticfiles/.
    outDir: 'static/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        styles: 'static/.tailwind/input.css',
        main: 'static/js/main.js'
      },
      output: {
        entryFileNames: 'js/[name].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'styles.css') {
            return 'css/styles.css'
          }
          return assetInfo.name
        }
      }
    }
  }
})
