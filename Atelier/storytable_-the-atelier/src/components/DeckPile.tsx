import React from "react";
import { motion } from "motion/react";
import { CardType } from "../types";
import { User, Heart, MapPin, Clock, Flame, Film, CloudRain, Eye, Music, Package, Lightbulb, HelpCircle, Plus } from "lucide-react";

interface DeckPileProps {
  type: CardType;
  label: string;
  color: string;
  onDraw: () => void;
  disabled?: boolean;
}

const ICONS: Record<CardType, React.ReactNode> = {
  character:    <User size={24} />,
  relationship: <Heart size={24} />,
  space:        <MapPin size={24} />,
  timeline:     <Clock size={24} />,
  element:      <Flame size={24} />,
  cinematic:    <Film size={24} />,
  mood:         <CloudRain size={24} />,
  sense:        <Eye size={24} />,
  audio:        <Music size={24} />,
  prop:         <Package size={24} />,
  concept:      <Lightbulb size={24} />,
  guide:        <HelpCircle size={24} />,
};

const DeckPile: React.FC<DeckPileProps> = ({ type, label, color, onDraw, disabled }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.08, y: -4 }}
      whileTap={{ scale: 0.92 }}
      onClick={onDraw}
      disabled={disabled}
      className={`relative w-16 h-22 rounded-xl ${color} text-white shadow-lg flex flex-col items-center justify-center gap-1 overflow-hidden disabled:opacity-40 disabled:cursor-not-allowed transition-all`}
      style={{ minHeight: '5.5rem' }}
    >
      <div className="absolute inset-0 opacity-10 workshop-grain" />
      <div className="absolute -bottom-0.5 w-[85%] h-0.5 bg-white/20 rounded-full blur-xs" />

      <div className="relative z-10 p-1.5 rounded-lg bg-white/20 backdrop-blur-md">
        {ICONS[type]}
      </div>

      <span className="relative z-10 text-[8px] font-bold uppercase tracking-wider text-center leading-tight opacity-90">
        {label}
      </span>

      <div className="absolute bottom-1 right-1 p-0.5 bg-white/25 rounded-full">
        <Plus size={8} />
      </div>
    </motion.button>
  );
};

export default DeckPile;
