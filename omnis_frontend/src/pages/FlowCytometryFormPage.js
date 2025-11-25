import Navbar from "../components/Navbar";
import FlowCytometryForm from "../components/forms/FlowCytometryForm";
import { useParams } from "react-router-dom";

const FlowCytometryFormPage = () => {
    
    const {progressive_id} = useParams();

    return (
        <>
        <Navbar/>
        <FlowCytometryForm projectId={progressive_id}/>
        </>
    );
};

export default FlowCytometryFormPage;