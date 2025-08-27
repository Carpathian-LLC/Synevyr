'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';

type LogLine = {
  text: string;
  type: 'info' | 'command' | 'output' | 'error';
};

export default function NotFound() {
  const pathname = usePathname() ?? '';
  const searchParams = useSearchParams();
  const queryString = searchParams.toString();
  const fullPath = pathname + (queryString ? `?${queryString}` : '');

  // Keep track of when this terminal session started
  const startTimeRef = useRef<Date>(new Date());
  // For auto-scrolling
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Prepare initial 404 + curl lines
  const initialLogs = useMemo<LogLine[]>(() => {
    return [
      { text: 'Error 404: Page not found.', type: 'info' },
      {
        text:
          'curl ' +
          (typeof window !== 'undefined' ? window.location.origin : '') +
          fullPath,
        type: 'command',
      },
    ];
  }, [fullPath]);


  const [logs, setLogs] = useState<LogLine[]>(initialLogs);
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset on path change
  useEffect(() => {
    setLogs(initialLogs);
    setInput('');
    inputRef.current?.focus();
    }, [fullPath, initialLogs]);


  // Auto-scroll to bottom on every logs change
  useEffect(() => {
    const el = logsContainerRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [logs]);

  // Built-in frontend commands — just add more keys here!
  const commands: Partial<Record<string, (args: string[]) => string[]>> = {
    help: (args) => {
      if (args.length === 0) {
        return [
          'Available commands:',
          '  help, about, echo, date, time, whoami, path, version, clear, ls, cd, joke, secret, open-sesame, sudo,',
          '  ping, uptime, random, fortune, calc, ip, browser, inspire, weather, ascii',
          'Type `help [command]` for details.',
        ];
      }
      const cmd = args[0].toLowerCase();
      const details: Record<string, string[]> = {
        echo: ['Usage: echo [text]', '  Prints the text back.'],
        date: ['Usage: date', '  Shows today’s date.'],
        time: ['Usage: time', '  Shows current time.'],
        clear: ['Usage: clear', '  Clears the terminal.'],
        ls: ['Usage: ls', '  Lists mock directories.'],
        cd: ['Usage: cd [dir]', '  Changes directory (not supported).'],
        help: ['Usage: help [command]', '  Shows this message.'],
        sudo: ['Usage: sudo [action]', '  Try “sudo make-me-a-sandwich”.'],
        'open-sesame': ['Usage: open-sesame', '  Reveals a secret vault.'],
        ping: ['Usage: ping', '  Tests connectivity (responds pong).'],
        uptime: ['Usage: uptime', '  Shows how long the session has been up.'],
        random: ['Usage: random', '  Generates a random number.'],
        fortune: ['Usage: fortune', '  Tells you a random fortune.'],
        calc: ['Usage: calc [expr]', '  Evaluates a simple math expression.'],
        ip: ['Usage: ip', '  Shows the origin URL.'],
        browser: ['Usage: browser', '  Shows your browser user agent.'],
        inspire: ['Usage: inspire', '  Gives you a motivational quote.'],
        weather: ['Usage: weather', '  Shows a mock weather report.'],
        ascii: ['Usage: ascii', '  Prints a small ASCII art.'],
      };
      return details[cmd] || [`No help entry for "${cmd}".`];
    },
    about: () => [
      'Carpathian Cloud',
      'A VM provisioning platform',
    ],
    version: () => ['Carpathian Cloud version 1.0.0'],
    echo: (args) => [args.join(' ')],
    date: () => [new Date().toLocaleDateString()],
    time: () => [new Date().toLocaleTimeString()],
    whoami: () => ['guest'],
    path: () => [fullPath],
    ls: () => ['dashboard  servers  docs  config password.txt'],
    cd: (args) => [
      `bash: cd: ${args.join(' ') || '~'}: No such file or directory`,
    ],
    joke: () => [
      'Why do programmers prefer dark mode?',
      'Because light attracts bugs! 🐞',
    ],
    secret: () => ['🤫 The secret code is 42… shh!'],
    'open-sesame': () => [
      '🔓 You’ve discovered the hidden vault!',
      'But it’s empty… for now.',
    ],
    sudo: (args) => {
      if (args.join(' ') === 'make-me-a-sandwich') {
        return ['Okay. Here’s your sandwich 🥪'];
      }
      if (args[0] === 'rm' && args[1] === '-rf') {
        return ["I'm sorry, Dave. I’m afraid I can’t do that."];
      }
      return ['sudo: command not found or permission denied.'];
    },
    ping: () => ['pong'],
    uptime: () => {
      const now = new Date();
      let delta = Math.floor(
        (now.getTime() - startTimeRef.current.getTime()) / 1000
      );
      const days = Math.floor(delta / 86400);
      delta %= 86400;
      const hours = Math.floor(delta / 3600);
      delta %= 3600;
      const minutes = Math.floor(delta / 60);
      const seconds = delta % 60;
      return [
        `Uptime: ${days}d ${hours}h ${minutes}m ${seconds}s`,
      ];
    },
    random: () => [Math.random().toString()],
    fortune: () => {
      const fortunes = [
        'You will have a productive day!',
        'Surprise is headed your way.',
        'Good news will come to you by mail.',
        'Fortune favors the bold.',
      ];
      return [fortunes[Math.floor(Math.random() * fortunes.length)]];
    },
    calc: (args) => {
      try {
        const expr = args.join(' ');
        const result = Function(`"use strict";return (${expr})`)();
        return [String(result)];
      } catch {
        return ['Error: invalid expression'];
      }
    },
    ip: () =>
      typeof window !== 'undefined'
        ? [`Origin: ${window.location.origin}`]
        : ['No window object.'],
    browser: () =>
      typeof navigator !== 'undefined'
        ? [`User-Agent: ${navigator.userAgent}`]
        : ['No navigator object.'],
    inspire: () => [
      '“Believe you can and you’re halfway there.” - Theodore Roosevelt',
    ],
    weather: () => ['Weather: Sunny, with a chance of sun.'],
    ascii: () => [
      '  /\\_/\\  ',
      " ( o.o ) ",
      '  > ^ <  ',
    ],
  };

  // Handle Enter key
  const onEnter = () => {
    const cmdLine = input.trim();
    if (!cmdLine) return;

    const commandLog: LogLine = { text: `> ${cmdLine}`, type: 'command' };
    const parts = cmdLine.split(/\s+/);
    const key = parts[0].toLowerCase();
    const args = parts.slice(1);

    if (key === 'clear') {
      setLogs(initialLogs);
    } else {
    const fn = commands[key];
    const raw = typeof fn === 'function' ? fn(args) : [`command not found: ${key}`];

      const outputLogs: LogLine[] = raw.map((line) => ({
        text: line,
        type: fn ? 'output' : 'error',
      }));
      setLogs((prev) => [...prev, commandLog, ...outputLogs]);
    }
    setInput('');
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      onClick={() => inputRef.current?.focus()}
    >
      <div className="w-[800px] h-[500px] bg-white bg-opacity-10 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-700 rounded-2xl shadow-lg p-4 flex flex-col font-mono text-sm text-white">
        {/* Logs area */}
        <div
          className="flex-1 overflow-y-auto mb-2"
          ref={logsContainerRef}
        >
          {/* Prominent 404 */}
          {logs.length > 0 && (
            <div className="text-2xl font-bold text-red-500 mb-4">
              {logs[0].text}
            </div>
          )}
          {/* All other lines */}
          {logs.slice(1).map((line, i) => {
            let cls = 'text-white';
            if (line.type === 'info' || line.type === 'error') {
              cls = 'text-[#F11C6B]';
            } else if (line.type === 'command') {
              cls = 'text-[#1B8FF2]';
            }
            return (
              <div key={i} className={`whitespace-pre-wrap ${cls}`}>
                {line.text}
              </div>
            );
          })}
        </div>
        {/* Input area */}
        <div className="flex items-center">
          <span className="text-[#F11C6B]">carpathian@cloud:~$</span>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onEnter()}
            className="ml-2 flex-1 bg-transparent focus:outline-none text-white"
          />
          <span className="ml-1 animate-pulse">█</span>
        </div>
      </div>
    </div>
  );
}
