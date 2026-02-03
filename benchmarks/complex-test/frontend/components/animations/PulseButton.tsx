'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface PulseButtonProps {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

export function PulseButton({
  children,
  onClick,
  className = '',
  disabled = false,
  type = 'button',
}: PulseButtonProps) {
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={className}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{
        type: 'spring',
        stiffness: 400,
        damping: 17,
      }}
    >
      {children}
    </motion.button>
  );
}
