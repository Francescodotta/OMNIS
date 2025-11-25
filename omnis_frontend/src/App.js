import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './permissions/ProtectedRoute';
import AdminRoute from './permissions/AdminRoute';
import MainPageUser from './pages/MainPageUser';
import LandingPage from './pages/LandingPage';
import CreateProjectForm from './components/ProjectForm';
import {AuthProvider} from './utils/AuthContext';
import AdminDashboard from './components/AdminDashboard';
import RegisterUser from './components/RegisterUser';
import ChangePasswordPage from './pages/ChangePassword';
import ProjectPage from './pages/ProjectPage';
import HandleMembers from './pages/HandleMembers';
import AddMemberPage from './pages/AddMember';
import BatchMetabolomicsUpload from './components/forms/BatchMetabolomicsUpload';
import BatchProteomicsUpload from './components/forms/BatchProteomicsUpload';
import DiagramDragDrop from './components/DiagramDragDrop';
import FC_Pipeline from './components/flow_cytometry/pipeline/FCPipeline';
import HandlePipeline from './pages/HandlePipeline';
import FlowCytometryFormPage from './pages/FlowCytometryFormPage';
import {ProjectProvider} from './context/ProjectContext';
import FlowCytometryBatchFormPage from './pages/FlowCytometryBatchFormPage';
import PipelineBuilder from './pages/PipelineBuilder';
import PipelineRunDashboard from './components/dashboards/PipelineRunDashboard';
import ProteomicsPipeline from './components/proteomics/pipeline/ProteomicsPipeline';
import ReportFCS from './pages/ReportFCS';
import GatingFlowCytometry from './pages/GatingFlowCytometry';
import UploadPage from './components/transcriptomics/UploadFile';
import GatingStrategyFormPage from './pages/flow_cytometry/GatingStrategyFormPage';
import GatingStrategyDashboardPage from './pages/flow_cytometry/GatingStrategyDashboardPage';
import Metabolomics_Pipeline from './components/pipelines/MetaboPipeline'
import RadiomicsFormPage from './pages/radiomics/RadiomicsFormPage';
import PipelineRunMetabolomicsDashboard from './components/dashboards/PipelineRunDashboardMetabolomics';
import ReportMetabolomicsPipeline from './pages/MetabolomicsReport'
import ProteomicsPipelineResultsDashboard from './components/proteomics/results/ProteomcisPipelineDashboard';
import StandardizedFields from './components/forms/StandardizedFields';

function App() {
  return (
    <AuthProvider>
      <ProjectProvider>
        <Router>
        <div className="App">
          <Routes>
            {/* Landing page */}
            <Route path='/' element={<LandingPage/>} />
            {/* User page */}
            <Route path='/user' element={<ProtectedRoute component={MainPageUser}/>}/>
            <Route path='/user/change-password' element={<ProtectedRoute component={ChangePasswordPage}/>}/>
            {/* Create project */}
            <Route path='/create-project' element={<ProtectedRoute component={CreateProjectForm}/>}/>
            {/* Admin page */}
            <Route path='/admin' element={<AdminRoute component={AdminDashboard}/>}/>
            {/* Register user */}
            <Route path='/admin/register-user' element={<AdminRoute component={RegisterUser}/>}/>
            {/* Project page */}
            <Route path='/project/:progressive_id' element={<ProtectedRoute component={ProjectPage}/>}/>
            {/* Handle members */}
            <Route path='/project/:progressive_id/members' element={<ProtectedRoute component={HandleMembers}/>}/>
            {/* Add member */}
            <Route path='/add-member/:progressive_id' element={<ProtectedRoute component={AddMemberPage}/>}/>
            {/* Metabolomics form */}
            <Route path='/project/:progressive_id/metabolomics/upload' element={<ProtectedRoute component={BatchMetabolomicsUpload}/>}/> 
            {/* Proteomics form */}
            <Route path='/project/:progressive_id/proteomics/upload' element={<ProtectedRoute component={BatchProteomicsUpload}/>}/>
            {/* Diagram drag drop */}
            <Route path='/project/:progressive_id/diagram' element={<ProtectedRoute component={DiagramDragDrop}/>}/>
            {/* Flow cytometry pipeline */}
            <Route path='/project/:progressive_id/diagram/flow_cytometry' element={<ProtectedRoute component={FC_Pipeline}/>}/>
            {/* Proteomics Pipeline */}
            <Route path='/project/:progressive_id/diagram/proteomics' element={<ProtectedRoute component={ProteomicsPipeline}/>}/>
            {/* Metabolomics Pipeline */}
            <Route path='/project/:progressive_id/diagram/metabolomics' element={<ProtectedRoute component={Metabolomics_Pipeline}/>}/>
            {/* Pipeline builder */}
            <Route path='/project/:progressive_id/diagram/PipelineBuilder' element={<ProtectedRoute component={PipelineBuilder}/>}/>
            {/* Pipeline run dashboard */}
            <Route path='/project/:progressive_id/running_pipelines' element={<ProtectedRoute component={PipelineRunDashboard}/>}/>
            {/* Metabolomics Pipeline Dashboard */}
            <Route path='/project/:progressive_id/metabolomics/running_pipelines' element={<ProtectedRoute component={PipelineRunMetabolomicsDashboard}/>}/>
            {/* Report FCS */}
            <Route path="/project/:projectId/report/:pipelineId" element={<ReportFCS />} />
            {/* Handle pipeline */}
            <Route path='/project/:progressive_id/pipelines' element={<ProtectedRoute component={HandlePipeline}/>}/>
            {/* Flow cytometry form */}
            <Route path='/project/:progressive_id/flow_cytometry/upload' element={<ProtectedRoute component={FlowCytometryFormPage}/>}/>
            {/* Flow cytometry batch form */}
            <Route path='/project/:progressive_id/flow_cytometry/upload_batch' element={<ProtectedRoute component={FlowCytometryBatchFormPage}/>}/>
            {/* route to create a new gating element */}
            <Route path='/project/:projectId/fcs_object/:progressiveId/gating_strategies/:gatingStrategyId/gating_elements' element={<ProtectedRoute component={GatingFlowCytometry}/>}/>
            {/* route to create a new gating strategy */}
            <Route path='/project/:projectId/fcs_object/:progressiveId/gatingStrategy/new' element={<ProtectedRoute component={GatingStrategyFormPage}/>}/>
            {/* route to get the gating strategies of a specific project */}
            <Route path='/project/:projectId/fcs_object/:progressiveId/gatingStrategies' element={<ProtectedRoute component={GatingStrategyDashboardPage}/>}/>
            {/* Route to edit an existing gating strategy */}
            <Route path='/project/:projectId/fcs_object/:progressiveId/gatingStrategy/edit/:gatingStrategyId' element={<ProtectedRoute component={GatingStrategyFormPage}/>}/>
            {/* Route to upload a transcriptomic file */}
            <Route path='/project/:projectId/transcriptomics/upload' element={<ProtectedRoute component={UploadPage}/>}/>
            {/* Route to upload the radiomics file */}
            <Route path='/project/:projectId/radiomics/upload' element={<ProtectedRoute component={RadiomicsFormPage}/>}/>

            {/* METABOLOMICS ROUTES */}
            <Route path = '/project/:projectId/metabolomics/pipeline/:pipelineId/report' element={<ProtectedRoute component={ReportMetabolomicsPipeline}/>}/>

            {/* PROTEOMICS ROUTES */}
            {/* RUNNING PIPELINES */}
            <Route path= '/project/:projectId/proteomics/pipelines' element={<ProtectedRoute component={ProteomicsPipelineResultsDashboard}/>}/>


            {/* STANDARDIZED FIELDS */}
            <Route path='/project/:projectId/standardized-fields' element={<ProtectedRoute component={StandardizedFields}/>}/>

      
          </Routes>
        </div>
        </Router>
      </ProjectProvider>
    </AuthProvider>
  );
}

export default App;
