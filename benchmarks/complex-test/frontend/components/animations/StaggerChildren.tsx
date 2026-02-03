'use client';

import { motion } from 'framer-motion';
import { ReactNode, Children } from 'react';

interface StaggerChildrenProps {
  children: ReactNode;
  staggerDelay?: number;
  initialDelay?: number;
  className?: string;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.25, 0.1, 0.25, 1],
    },
  },
};

export function StaggerChildren({
  children,
  staggerDelay = 0.1,
  initialDelay = 0,
  className = '',
}: StaggerChildrenProps) {
  const customContainerVariants = {
    ...containerVariants,
    visible: {
      ...containerVariants.visible,
      transition: {
        delayChildren: initialDelay,
        staggerChildren: staggerDelay,
      },
    },
  };

  return (
    <motion.div
      variants={customContainerVariants}
      initial="hidden"
      animate="visible"
      className={className}
    >
      {Children.map(children, (child) => (
        <motion.div variants={itemVariants}>{child}</motion.div>
      ))}
    </motion.div>
  );
}
