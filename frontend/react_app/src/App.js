import React, { useState, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Container,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
} from "@mui/material";

//const url = "http://localhost:8000"
const url = "http://agent-back.lottotry.com:8000"

function App() {
  const [prompt, setPrompt] = useState("");
  const [results, setResults] = useState([]);

  const submitPrompt = async () => {
    const res = await axios.post("http://agent-back.lottotry.com:8000/api/query", null, {
      params: { prompt },
    });
    setResults([...results, res.data]);
  };

  useEffect(() => {
    axios
      .get("http://agent-back.lottotry.com:8000/api/results")
      .then((res) => setResults(res.data));
  }, []);

  return (
    <Container maxWidth="md">
      <TextField
        fullWidth
        label="Enter your prompt"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <Button variant="contained" sx={{ mt: 2 }} onClick={submitPrompt}>
        Run Agents
      </Button>

      {results.map((r) => (
        <Card key={r.id} sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mt: 0, color: "green" }}>
              Prompt
            </Typography>
            <Typography>{r.prompt}</Typography>
            <Typography variant="h6" sx={{ mt: 5, color: "green" }}>
              Results
            </Typography>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {r.results}
            </ReactMarkdown>
          </CardContent>
        </Card>
      ))}
    </Container>
  );
}

export default App;
