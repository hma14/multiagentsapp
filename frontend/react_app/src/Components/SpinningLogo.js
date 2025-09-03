import { Box } from "@mui/material";

const SpinningLogo = ({ size = 60 }) => (
  <Box
    component="img"
    src="./logo192.png"
    alt="Agent Search Logo"
    sx={{
      //width: size,
      mt: 1,
      mr: 2,
      height: size,
      animation: "spin 10s linear infinite",
      "@keyframes spin": {
        "0%": { transform: "rotate(0deg)" },
        "100%": { transform: "rotate(360deg)" },
      },
    }}
  />
);

export default SpinningLogo;
