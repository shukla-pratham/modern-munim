import { Bell, Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export function TopBar({ title }: { title: string }) {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  return (
    <header className="h-16 border-b border-border flex items-center justify-between px-6 bg-background/80 backdrop-blur-md sticky top-0 z-20">
      <motion.h1
        className="text-lg font-semibold text-foreground"
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
        key={title}
      >
        {title}
      </motion.h1>

      <div className="flex items-center gap-2">
        <button className="p-2 rounded-lg hover:bg-accent transition-colors relative">
          <Bell className="h-4.5 w-4.5 text-muted-foreground" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-magenta rounded-full" />
        </button>
        <button
          onClick={() => setDark(!dark)}
          className="p-2 rounded-lg hover:bg-accent transition-colors"
        >
          <motion.div
            initial={false}
            animate={{ rotate: dark ? 0 : 180 }}
            transition={{ duration: 0.3 }}
          >
            {dark ? (
              <Moon className="h-4.5 w-4.5 text-muted-foreground" />
            ) : (
              <Sun className="h-4.5 w-4.5 text-muted-foreground" />
            )}
          </motion.div>
        </button>
      </div>
    </header>
  );
}
