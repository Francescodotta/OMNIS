"use client"

import { useState, useEffect } from "react"
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  useMediaQuery,
  useTheme,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Badge,
} from "@mui/material"
import { Link, useLocation } from "react-router-dom"
import {
  Home,
  Settings,
  LogOut,
  MenuIcon,
  User,
  ChevronDown,
  X,
  Bell,
  HelpCircle,
  Database,
  BarChart2,
} from "lucide-react"

const Navbar = () => {
  const [role, setRole] = useState(null)
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down("md"))
  const location = useLocation()

  const [anchorEl, setAnchorEl] = useState(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [notificationsAnchorEl, setNotificationsAnchorEl] = useState(null)

  // Use useEffect to safely access localStorage
  useEffect(() => {
    setRole(localStorage.getItem("role"))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("role")
    window.location.reload()
  }

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget)
  }

  const handleProfileMenuClose = () => {
    setAnchorEl(null)
  }

  const handleNotificationsOpen = (event) => {
    setNotificationsAnchorEl(event.currentTarget)
  }

  const handleNotificationsClose = () => {
    setNotificationsAnchorEl(null)
  }

  const toggleDrawer = (open) => () => {
    setDrawerOpen(open)
  }

  const isActive = (path) => {
    return location.pathname === path
  }

  // Only render menus when their anchor elements exist
  const profileMenuOpen = Boolean(anchorEl)
  const notificationsMenuOpen = Boolean(notificationsAnchorEl)

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: "background.paper",
        color: "text.primary",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Toolbar sx={{ justifyContent: "space-between" }}>
        {/* Logo and Home Button */}
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <Box sx={{ display: "flex", alignItems: "center", mr: 2 }}>
            <Database size={24} color={theme.palette.primary.main} />
            <Typography
              variant="h6"
              component="div"
              sx={{
                ml: 1,
                fontWeight: "bold",
                display: { xs: "none", sm: "block" },
              }}
            >
              OMNIS
            </Typography>
          </Box>

          {!isMobile && (
            <Box sx={{ display: "flex" }}>
              <Button
                component={Link}
                to="/user"
                startIcon={<Home size={18} />}
                sx={{
                  mx: 0.5,
                  fontWeight: isActive("/user") ? "bold" : "normal",
                  color: isActive("/user") ? "primary.main" : "text.primary",
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                Home
              </Button>

              <Button
                component={Link}
                to="/user"
                startIcon={<Database size={18} />}
                sx={{
                  mx: 0.5,
                  fontWeight: isActive("/user") ? "bold" : "normal",
                  color: isActive("/user") ? "primary.main" : "text.primary",
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                Projects
              </Button>

              <Button
                component={Link}
                to="/user"
                startIcon={<BarChart2 size={18} />}
                sx={{
                  mx: 0.5,
                  fontWeight: isActive("/user") ? "bold" : "normal",
                  color: isActive("/user") ? "primary.main" : "text.primary",
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                Analytics
              </Button>

              {role === "admin" && (
                <Button
                  component={Link}
                  to="/admin"
                  startIcon={<Settings size={18} />}
                  sx={{
                    mx: 0.5,
                    fontWeight: isActive("/admin") ? "bold" : "normal",
                    color: isActive("/admin") ? "primary.main" : "text.primary",
                    "&:hover": { bgcolor: "action.hover" },
                  }}
                >
                  Admin
                </Button>
              )}
            </Box>
          )}
        </Box>

        {/* Right side buttons */}
        <Box sx={{ display: "flex", alignItems: "center" }}>
          {!isMobile && (
            <>
              <Tooltip title="Help">
                <IconButton color="inherit" sx={{ ml: 1 }}>
                  <HelpCircle size={20} />
                </IconButton>
              </Tooltip>

              <Tooltip title="Notifications">
                <IconButton color="inherit" sx={{ ml: 1 }} onClick={handleNotificationsOpen}>
                  <Badge badgeContent={2} color="primary">
                    <Bell size={20} />
                  </Badge>
                </IconButton>
              </Tooltip>
            </>
          )}

          {isMobile ? (
            <IconButton edge="end" color="inherit" onClick={toggleDrawer(true)} sx={{ ml: 1 }}>
              <MenuIcon size={24} />
            </IconButton>
          ) : (
            <Tooltip title="Account settings">
              <Button
                onClick={handleProfileMenuOpen}
                startIcon={
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: "primary.main",
                      fontSize: "0.875rem",
                    }}
                  >
                    <User size={18} />
                  </Avatar>
                }
                endIcon={<ChevronDown size={16} />}
                sx={{
                  textTransform: "none",
                  color: "text.primary",
                  ml: 1,
                  "&:hover": { bgcolor: "action.hover" },
                }}
              >
                Account
              </Button>
            </Tooltip>
          )}
        </Box>
      </Toolbar>

      {/* Only render menus when their anchor elements exist */}
      {profileMenuOpen && (
        <Menu
          anchorEl={anchorEl}
          open={profileMenuOpen}
          onClose={handleProfileMenuClose}
          PaperProps={{
            elevation: 3,
            sx: {
              mt: 1.5,
              borderRadius: 2,
              minWidth: 200,
            },
          }}
          anchorOrigin={{
            vertical: "bottom",
            horizontal: "right",
          }}
          transformOrigin={{
            vertical: "top",
            horizontal: "right",
          }}
          disableScrollLock
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
              User Account
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {role === "admin" ? "Administrator" : "User"}
            </Typography>
          </Box>
          <Divider />
          <MenuItem
            component={Link}
            to="/user/change-password"
            onClick={handleProfileMenuClose}
            sx={{
              py: 1.5,
              "&:hover": { bgcolor: "action.hover" },
            }}
          >
            <ListItemIcon>
              <Settings size={18} />
            </ListItemIcon>
            <ListItemText>Change Password</ListItemText>
          </MenuItem>
          {role === "admin" && (
            <MenuItem
              component={Link}
              to="/admin"
              onClick={handleProfileMenuClose}
              sx={{
                py: 1.5,
                "&:hover": { bgcolor: "action.hover" },
              }}
            >
              <ListItemIcon>
                <Settings size={18} />
              </ListItemIcon>
              <ListItemText>Admin Dashboard</ListItemText>
            </MenuItem>
          )}
          <Divider />
          <MenuItem
            onClick={() => {
              handleProfileMenuClose()
              handleLogout()
            }}
            sx={{
              py: 1.5,
              color: "error.main",
              "&:hover": { bgcolor: "error.light", color: "error.dark" },
            }}
          >
            <ListItemIcon>
              <LogOut size={18} color="error" />
            </ListItemIcon>
            <ListItemText>Logout</ListItemText>
          </MenuItem>
        </Menu>
      )}

      {notificationsMenuOpen && (
        <Menu
          anchorEl={notificationsAnchorEl}
          open={notificationsMenuOpen}
          onClose={handleNotificationsClose}
          PaperProps={{
            elevation: 3,
            sx: {
              mt: 1.5,
              borderRadius: 2,
              minWidth: 320,
              maxWidth: 320,
            },
          }}
          anchorOrigin={{
            vertical: "bottom",
            horizontal: "right",
          }}
          transformOrigin={{
            vertical: "top",
            horizontal: "right",
          }}
          disableScrollLock
        >
          <Box sx={{ px: 2, py: 1, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
              Notifications
            </Typography>
            <Button size="small" color="primary">
              Mark all as read
            </Button>
          </Box>
          <Divider />
          <Box sx={{ maxHeight: 320, overflow: "auto" }}>
            <MenuItem sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: "flex", flexDirection: "column", width: "100%" }}>
                <Typography variant="body2" sx={{ fontWeight: "medium" }}>
                  Pipeline "FCS Analysis" completed
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  2 minutes ago
                </Typography>
              </Box>
            </MenuItem>
            <MenuItem sx={{ py: 1.5, px: 2 }}>
              <Box sx={{ display: "flex", flexDirection: "column", width: "100%" }}>
                <Typography variant="body2" sx={{ fontWeight: "medium" }}>
                  New dataset uploaded
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  1 hour ago
                </Typography>
              </Box>
            </MenuItem>
            <Divider />
            <Box sx={{ p: 2, textAlign: "center" }}>
              <Button size="small" component={Link} to="/notifications">
                View all notifications
              </Button>
            </Box>
          </Box>
        </Menu>
      )}

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={toggleDrawer(false)}
        PaperProps={{
          sx: { width: 280 },
        }}
      >
        <Box sx={{ p: 2, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: "bold" }}>
            Menu
          </Typography>
          <IconButton onClick={toggleDrawer(false)}>
            <X size={20} />
          </IconButton>
        </Box>
        <Divider />
        <List>
          <ListItem button component={Link} to="/user" onClick={toggleDrawer(false)} selected={isActive("/user")}>
            <ListItemIcon>
              <Home size={20} color={isActive("/user") ? "primary" : "inherit"} />
            </ListItemIcon>
            <ListItemText primary="Home" />
          </ListItem>
          <ListItem
            button
            component={Link}
            to="/user"
            onClick={toggleDrawer(false)}
            selected={isActive("/user")}
          >
            <ListItemIcon>
              <Database size={20} color={isActive("/user") ? "primary" : "inherit"} />
            </ListItemIcon>
            <ListItemText primary="Projects" />
          </ListItem>
          <ListItem
            button
            component={Link}
            to="/user"
            onClick={toggleDrawer(false)}
            selected={isActive("/user")}
          >
            <ListItemIcon>
              <BarChart2 size={20} color={isActive("/user") ? "primary" : "inherit"} />
            </ListItemIcon>
            <ListItemText primary="Analytics" />
          </ListItem>
          {role === "admin" && (
            <ListItem button component={Link} to="/admin" onClick={toggleDrawer(false)} selected={isActive("/admin")}>
              <ListItemIcon>
                <Settings size={20} color={isActive("/admin") ? "primary" : "inherit"} />
              </ListItemIcon>
              <ListItemText primary="Admin Dashboard" />
            </ListItem>
          )}
          <ListItem
            button
            component={Link}
            to="/user/change-password"
            onClick={toggleDrawer(false)}
            selected={isActive("/user/change-password")}
          >
            <ListItemIcon>
              <Settings size={20} color={isActive("/user/change-password") ? "primary" : "inherit"} />
            </ListItemIcon>
            <ListItemText primary="Change Password" />
          </ListItem>
        </List>
        <Divider />
        <List>
          <ListItem button onClick={handleLogout} sx={{ color: "error.main" }}>
            <ListItemIcon>
              <LogOut size={20} color="error" />
            </ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItem>
        </List>
      </Drawer>
    </AppBar>
  )
}

export default Navbar

