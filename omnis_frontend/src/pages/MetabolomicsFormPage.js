import Navbar from "../components/Navbar";
import MetabolomicsForm from "../components/forms/MetabolomicsForm";
import { useParams } from "react-router-dom";

const MetabolomicsFormPage = () => {
    
    const {progressive_id} = useParams();

    return (
        <>
        <Navbar/>
        <MetabolomicsForm projectId={progressive_id}/>
        </>
    );
};

export default MetabolomicsFormPage;