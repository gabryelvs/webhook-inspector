import { useParams } from "react-router-dom";

export default function BinPage() {
  const { binId } = useParams();
  return <main className="p-8">Bin: {binId}</main>;
}
