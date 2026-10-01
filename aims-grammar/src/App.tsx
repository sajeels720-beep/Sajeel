import { MotionConfig } from "motion/react";
import { Nav } from "./components/Nav";
import { HeroStack } from "./components/Hero";
import { Vision } from "./components/Vision";
import { Journey } from "./components/Journey";
import { Values } from "./components/Values";
import { Life } from "./components/Life";
import { Admissions } from "./components/Admissions";
import { Footer, MobileActionBar, Visit } from "./components/Visit";

export default function App() {
  return (
    // reducedMotion="user": Motion drops transform/scroll animations for visitors who ask the OS for less motion.
    <MotionConfig reducedMotion="user">
      <Nav />
      <main id="main">
        <HeroStack>
          <Vision />
        </HeroStack>
        <Journey />
        <Values />
        <Life />
        <Admissions />
        <Visit />
      </main>
      <Footer />
      <MobileActionBar />
    </MotionConfig>
  );
}
