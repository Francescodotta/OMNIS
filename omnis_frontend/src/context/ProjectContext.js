import React, { createContext, useContext, useState } from 'react';

const ProjectContext = createContext();

export const ProjectProvider = ({ children }) => {
    const [projectData, setProjectData] = useState(null);
    const [projectType, setProjectType] = useState(null); // Inizialmente null

    const resetProject = () => {
        setProjectData(null);
        setProjectType(null); // Resetta il tipo di progetto a null
    };

    return (
        <ProjectContext.Provider value={{ projectData, setProjectData, projectType, setProjectType, resetProject }}>
            {children}
        </ProjectContext.Provider>
    );
};

export const useProject = () => useContext(ProjectContext);