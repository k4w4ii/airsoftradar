"use client";
import { useState } from "react";
import { imgSrc } from "../lib/links";

// Kategória-csempe képe: ha a bolt nem engedi a kép betöltését, a következő jelöltet próbálja; ha egyik sem megy, eltűnik
export default function CatImg({ srcs = [], alt = "" }) {
  srcs = srcs.map(imgSrc).filter(Boolean);
  const [i, setI] = useState(0);
  if (i >= srcs.length) return null;
  return <img key={srcs[i]} src={srcs[i]} alt={alt} loading="lazy" referrerPolicy="no-referrer" onError={() => setI(i + 1)} />;
}
