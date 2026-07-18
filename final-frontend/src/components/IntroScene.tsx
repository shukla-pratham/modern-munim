import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function Ring() {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.x += delta * 0.2;
      ref.current.rotation.y += delta * 0.3;
    }
  });

  return (
    <mesh ref={ref}>
      <torusGeometry args={[2, 0.04, 16, 100]} />
      <meshStandardMaterial color="#2563EB" emissive="#2563EB" emissiveIntensity={0.5} transparent opacity={0.6} />
    </mesh>
  );
}

function SecondRing() {
  const ref = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta * 0.15;
      ref.current.rotation.z += delta * 0.25;
    }
  });

  return (
    <mesh ref={ref} rotation={[Math.PI / 3, 0, 0]}>
      <torusGeometry args={[1.6, 0.02, 16, 80]} />
      <meshStandardMaterial color="#06B6D4" emissive="#06B6D4" emissiveIntensity={0.4} transparent opacity={0.4} />
    </mesh>
  );
}

export default function IntroScene() {
  return (
    <Canvas camera={{ position: [0, 0, 6], fov: 45 }} style={{ position: 'absolute', inset: 0 }}>
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={0.5} />
      <Ring />
      <SecondRing />
    </Canvas>
  );
}
