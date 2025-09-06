import React, { useState, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import SpinningLogo from "./Components/SpinningLogo";
import {
  Container,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import dayjs from "dayjs";
import CircularProgress from "@mui/material/CircularProgress";
import "./App.css";

//const url = "http://localhost:8000";
const url = "http://agent-back.lottotry.com:8000";

function App() {
  const [prompt, setPrompt] = useState("");
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const submitPrompt = async () => {
    setIsLoading(true);
    const res = await axios.post(`${url}/api/query`, null, {
      params: { prompt },
    });
    setResults([res.data, ...results]);
    setIsLoading(false);
  };

  useEffect(() => {
    axios.get(`${url}/api/results`).then((res) => setResults(res.data));
  }, []);

  return (
    <Container maxWidth="md">
      {isLoading ? (
        <div className="loader-container">
          <CircularProgress size={100} />
        </div>
      ) : (
        ""
      )}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
        }}
      >
        {/*
        <SpinningLogo />
         <Typography
          variant="h4"
          sx={{
            mt: 2,
            color: "green",
            textAlign: "center",
            fontWeight: "bold",
            fontFamily: "Arial, sans-serif",
            fontSize: 30,
          }}
        >
          Search by Agents
        </Typography> */}

        <SpinningLogo />
        <TextField
          fullWidth
          label="Enter your prompt"
          value={prompt}
          sx={{
            mt: 2,
            "& .MuiOutlinedInput-root": {
              borderRadius: "20px", // round the input box
            },
          }}
          onChange={(e) => setPrompt(e.target.value)}
        />
      </Box>
      <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
        <Button
          variant="contained"
          alignItems="right"
          sx={{
            mt: 2,
            borderRadius: "5px", // fully rounded pill style
            backgroundColor: "primary",
            fontSize: 12,
            display: "flex",
            alignItems: "right",
          }}
          onClick={submitPrompt}
          disabled={isLoading}
        >
          Submit
        </Button>
      </Box>

      {results.map((r) => (
        <Card key={r.id} sx={{ mt: 3 }}>
          <CardContent>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography sx={{ fontWeight: "bold", color: "green" }}>
                  {r.prompt}
                  <Typography
                    variant="caption"
                    sx={{
                      ml: 2,
                      fontFamily: "-moz-initial",
                      color: "ActiveCaption",
                    }}
                  >
                    {dayjs(r.createdAt).format("MMM D, YYYY • h:mm A")}
                  </Typography>
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {r.results}
                </ReactMarkdown>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
      ))}
    </Container>
  );
}

export default App;
