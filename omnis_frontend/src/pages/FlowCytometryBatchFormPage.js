import Navbar from "../components/Navbar";
import BatchUpload from "../components/forms/BatchFlowCytometryUpload";
import { useParams } from "react-router-dom";

const FlowCytometryBatchFormPage = () => {
    
    const {progressive_id} = useParams();

    return (
        <>
        <BatchUpload projectId={progressive_id}/>
        </>
    );
};

export default FlowCytometryBatchFormPage;