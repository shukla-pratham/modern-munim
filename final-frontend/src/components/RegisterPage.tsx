import { Navigate } from 'react-router-dom';

/** Registration is folded into the single Welcome / Sign In flow. */
export default function RegisterPage() {
  return <Navigate to="/" replace />;
}
